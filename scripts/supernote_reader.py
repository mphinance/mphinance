#!/usr/bin/env python3
"""
📓 Supernote → GitHub Issue pipeline.

Michael writes handwritten notes on a Supernote tablet. They export to PDFs in a
shared Google Drive folder. This script:

  1. Lists PDFs in the Drive folder (service-account auth).
  2. Downloads new ones and renders each page to a high-res PNG (PyMuPDF / fitz).
  3. Sends each page to Gemini vision to transcribe the handwriting AND pull the
     right-column margin tag.
  4. Maps that tag to a TARGET REPO via REPO_MAP below.
  5. Files a GitHub issue (full transcription + provenance) in that repo.

De-dupe is by Drive file id in a gitignored state file (`.supernote_seen.json`).

This is the new behavior: in the original pipeline the right-column tag routed a
note to a *system* (Sam / Blog / Gemini Agent). Now the tag names a *repo*, and
each tagged note becomes a GitHub issue in that repo.

Heavy third-party imports (google-genai, google-api-python-client, PyMuPDF) are
loaded lazily so `--help` and basic argument parsing work without them installed.

Modes:
  --check     verify Drive auth and list the folder. No transcription, no issues.
  --dry-run   download + transcribe + print the issues that WOULD be filed.
  (default)   full run: transcribe and create GitHub issues.

Env / secrets required for a full run:
  GOOGLE_APPLICATION_CREDENTIALS  path to the service-account JSON
                                  (falls back to ./service_account.json)
  GEMINI_API_KEY                  Gemini API key (vision transcription)
  GH_PAT                          GitHub PAT with `repo` scope (CROSS-REPO).
                                  The default Actions GITHUB_TOKEN is single-repo
                                  and CANNOT open issues in other repos, so a PAT
                                  is required here.

Manual one-time setup: share the Drive folder with the service account's email
(the `client_email` field in the JSON) so it can read the PDFs.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────

# The Supernote EXPORT folder on Google Drive (shared "anyone with the link").
# Same id hardcoded in GEMINI.md and AGENTS.md.
DRIVE_FOLDER_ID = "1UCPHJBoZSo9a0mP3O0eW8C7ra5kbmZjk"

# Gemini vision model used to read the handwriting.
GEMINI_MODEL = "gemini-2.5-flash"

# Zoom factor for rendering PDF pages to PNG. ~2x gives Gemini crisp handwriting
# without ballooning the image size.
RENDER_ZOOM = 2.0

# State file (gitignored) that records which Drive file ids we've already filed,
# so re-runs don't double-file. Lives at the repo root.
SEEN_STATE_FILE = Path(__file__).resolve().parent.parent / ".supernote_seen.json"

# ─── REPO MAP (EDIT ME) ───────────────────────────────────────────────────────
# Maps a right-column margin tag (lower-cased) to a "owner/repo" GitHub slug.
# Handwriting is messy, so keep keys short and add aliases generously. Matching
# is case-insensitive and ignores surrounding punctuation/whitespace.
#
# Unknown or missing tag → the note is SKIPPED and logged (never filed). Add a
# new alias here to route a tag you keep writing.
REPO_MAP = {
    "mphinance":   "mphinance/mphinance",

    "tickertrace": "mphinance/TickerTrace",
    "tt":          "mphinance/TickerTrace",

    # NOTE: Michael has 3 TraderDaddy repos. `traderdaddy-trade` is the
    # actively-developed one. The others are TraderDaddy-Pro---Whop and
    # TraderDaddy-Desktop. Edit the slugs below to retarget a tag.
    "traderdaddy": "mphinance/traderdaddy-trade",
    "td":          "mphinance/traderdaddy-trade",
    "tdpro":       "mphinance/traderdaddy-trade",
}

# Labels applied to every auto-filed issue. Created if missing (best-effort).
ISSUE_LABELS = ["supernote", "auto-filed"]

# Google Drive read-only scope.
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# ──────────────────────────────────────────────────────────────────────────────


def _log(msg: str) -> None:
    """Single place to print so output is easy to grep / redirect."""
    print(msg, flush=True)


def _normalize_tag(raw: str) -> str:
    """Lower-case a detected tag and strip anything that isn't a letter/number.

    Handwriting transcription is noisy ("T.D." / "td:" / "Trader Daddy"), so we
    collapse to a comparable key. We also fold spaces out so "trader daddy"
    matches "traderdaddy".
    """
    return re.sub(r"[^a-z0-9]", "", (raw or "").lower())


# Pre-normalize the repo map keys once so lookups are tolerant of messy tags.
_NORMALIZED_REPO_MAP = {_normalize_tag(k): v for k, v in REPO_MAP.items()}


def resolve_repo(tag: str):
    """Return the 'owner/repo' slug for a tag, or None if unknown/empty."""
    return _NORMALIZED_REPO_MAP.get(_normalize_tag(tag))


# ─── STATE (de-dupe) ──────────────────────────────────────────────────────────

def load_seen() -> dict:
    """Load the de-dupe state. Shape: {drive_file_id: {filed_at, repos: [...]}}."""
    if SEEN_STATE_FILE.exists():
        try:
            return json.loads(SEEN_STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            _log(f"  [WARN] Could not read {SEEN_STATE_FILE.name} ({e}); starting fresh.")
    return {}


def save_seen(seen: dict) -> None:
    SEEN_STATE_FILE.write_text(json.dumps(seen, indent=2), encoding="utf-8")


# ─── GOOGLE DRIVE ─────────────────────────────────────────────────────────────

def _creds_path() -> str:
    """Resolve the service-account JSON path, or exit with instructions."""
    path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or "service_account.json"
    if not os.path.exists(path):
        _log(
            "❌ No Google service-account credentials found.\n"
            f"   Looked for: $GOOGLE_APPLICATION_CREDENTIALS and ./service_account.json\n"
            "   Fix:\n"
            "     1. Create a service account in Google Cloud and download its JSON key.\n"
            "     2. Point GOOGLE_APPLICATION_CREDENTIALS at it (or save it as\n"
            "        ./service_account.json — already gitignored).\n"
            "     3. Share the Supernote Drive folder with the service account's\n"
            "        client_email so it can read the PDFs."
        )
        sys.exit(2)
    return path


def build_drive_service():
    """Build an authenticated Drive client from the service-account JSON."""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError:
        _log(
            "❌ google-api-python-client / google-auth not installed.\n"
            "   Install with: pip install -r scripts/requirements.txt"
        )
        sys.exit(2)

    path = _creds_path()
    creds = service_account.Credentials.from_service_account_file(path, scopes=DRIVE_SCOPES)
    # cache_discovery=False avoids a noisy warning and a write to a temp cache.
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def list_pdfs(service) -> list:
    """List PDF files in the Supernote folder, newest first.

    Returns a list of {id, name, modifiedTime} dicts.
    """
    query = (
        f"'{DRIVE_FOLDER_ID}' in parents "
        "and mimeType='application/pdf' "
        "and trashed=false"
    )
    files = []
    page_token = None
    while True:
        resp = (
            service.files()
            .list(
                q=query,
                fields="nextPageToken, files(id, name, modifiedTime)",
                orderBy="modifiedTime desc",
                pageSize=100,
                pageToken=page_token,
            )
            .execute()
        )
        files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return files


def download_pdf(service, file_id: str) -> bytes:
    """Download a Drive file's bytes into memory."""
    from googleapiclient.http import MediaIoBaseDownload
    import io

    request = service.files().get_media(fileId=file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buffer.getvalue()


# ─── PDF → PNG ────────────────────────────────────────────────────────────────

def render_pages(pdf_bytes: bytes) -> list:
    """Render each PDF page to PNG bytes at RENDER_ZOOM. Returns [png_bytes, ...]."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        _log(
            "❌ PyMuPDF (pymupdf) not installed.\n"
            "   Install with: pip install -r scripts/requirements.txt"
        )
        sys.exit(2)

    pages = []
    matrix = fitz.Matrix(RENDER_ZOOM, RENDER_ZOOM)
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            pix = page.get_pixmap(matrix=matrix)
            pages.append(pix.tobytes("png"))
    return pages


# ─── GEMINI VISION ────────────────────────────────────────────────────────────

# Asks for strict JSON so we can route reliably. The model returns one tag per
# page (the dominant right-column margin tag) plus the full transcription.
_VISION_PROMPT = """You are reading a single page of a handwritten Supernote notebook.

Do two things and return ONLY a JSON object (no markdown fences):

1. "transcription": Transcribe ALL handwritten text on the page as faithfully as
   possible, preserving line breaks. If a word is unreadable, write [?].
2. "tag": The note is routed by a short tag written in the RIGHT-COLUMN MARGIN
   (a word set off to the right edge of the page, separate from the main body).
   Return that tag verbatim as a string. Common tags name a project/repo such as
   "mphinance", "TickerTrace", "TT", "TraderDaddy", "TD". If there is no
   right-column tag, return an empty string.
3. "title": A concise (<= 70 char) summary of the note suitable as an issue title.
4. "date": Any date written on the page in YYYY-MM-DD form, else empty string.

Return exactly: {"transcription": "...", "tag": "...", "title": "...", "date": "..."}
"""


def transcribe_page(client, png_bytes: bytes) -> dict:
    """Send one page PNG to Gemini and parse its JSON response.

    Returns {transcription, tag, title, date}. On parse failure, falls back to a
    raw transcription with an empty tag (so it gets skipped, not mis-filed).
    """
    from google.genai import types

    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            types.Part.from_bytes(data=png_bytes, mime_type="image/png"),
            _VISION_PROMPT,
        ],
    )
    text = (resp.text or "").strip()
    # Strip accidental ```json fences if the model adds them.
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        _log("  [WARN] Gemini did not return JSON; treating page as untagged.")
        return {"transcription": text, "tag": "", "title": "", "date": ""}
    return {
        "transcription": data.get("transcription", ""),
        "tag": data.get("tag", ""),
        "title": data.get("title", ""),
        "date": data.get("date", ""),
    }


def build_gemini_client():
    """Build the Gemini client, or exit if the SDK / key is missing."""
    try:
        from google import genai
    except ImportError:
        _log(
            "❌ google-genai not installed.\n"
            "   Install with: pip install -r scripts/requirements.txt"
        )
        sys.exit(2)

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        _log("❌ GEMINI_API_KEY is not set. Export it before a full or --dry-run.")
        sys.exit(2)
    return genai.Client(api_key=key)


# ─── GITHUB ISSUES ────────────────────────────────────────────────────────────

GITHUB_API = "https://api.github.com"


def _gh_session():
    """Build a requests session authed with GH_PAT, or exit with instructions."""
    import requests

    pat = os.environ.get("GH_PAT")
    if not pat:
        _log(
            "❌ GH_PAT is not set.\n"
            "   A cross-repo Personal Access Token with `repo` scope is required:\n"
            "   the default Actions GITHUB_TOKEN can only touch its own repo, but\n"
            "   this pipeline files issues in OTHER repos. Set GH_PAT to a fine-\n"
            "   grained or classic PAT that can open issues in the target repos."
        )
        sys.exit(2)
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {pat}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    return session


def _ensure_labels(session, repo: str) -> None:
    """Create the supernote/auto-filed labels in a repo if missing (best-effort)."""
    for label in ISSUE_LABELS:
        resp = session.post(
            f"{GITHUB_API}/repos/{repo}/labels",
            json={"name": label, "color": "5319e7"},
        )
        # 201 created, 422 already exists — both fine. Anything else: warn only.
        if resp.status_code not in (201, 422):
            _log(f"  [WARN] Could not ensure label '{label}' on {repo}: {resp.status_code}")


def create_issue(session, repo: str, title: str, body: str) -> str:
    """Create a GitHub issue and return its html_url. Raises on hard failure."""
    _ensure_labels(session, repo)
    resp = session.post(
        f"{GITHUB_API}/repos/{repo}/issues",
        json={"title": title, "body": body, "labels": ISSUE_LABELS},
    )
    if resp.status_code != 201:
        raise RuntimeError(
            f"GitHub issue creation failed for {repo}: "
            f"{resp.status_code} {resp.text[:300]}"
        )
    return resp.json().get("html_url", "")


def _issue_body(note: dict, source_name: str, page_num: int) -> str:
    """Assemble the issue body: transcription + provenance + auto-filed footer."""
    detected_date = note.get("date") or "unknown"
    transcription = note.get("transcription", "").strip() or "(no text transcribed)"
    return (
        f"{transcription}\n\n"
        "---\n\n"
        "**Provenance**\n\n"
        f"- Source PDF: `{source_name}`\n"
        f"- Page: {page_num}\n"
        f"- Detected date: {detected_date}\n"
        f"- Detected tag: `{note.get('tag', '')}`\n\n"
        "_Auto-filed from a Supernote handwritten note by "
        "`scripts/supernote_reader.py`._"
    )


# ─── PIPELINE ─────────────────────────────────────────────────────────────────

def cmd_check() -> int:
    """Verify Drive auth and list the folder. No transcription, no issues."""
    _log(f"🔍 Checking Drive access to folder {DRIVE_FOLDER_ID} ...")
    service = build_drive_service()
    pdfs = list_pdfs(service)
    _log(f"✅ Auth OK. {len(pdfs)} PDF(s) in the folder:")
    seen = load_seen()
    for f in pdfs:
        mark = "•" if f["id"] in seen else "NEW"
        _log(f"  [{mark}] {f['name']}  ({f['modifiedTime']})  id={f['id']}")
    new_count = sum(1 for f in pdfs if f["id"] not in seen)
    _log(f"\n{new_count} new, {len(pdfs) - new_count} already processed.")
    return 0


def run_pipeline(dry_run: bool) -> int:
    """Full pipeline. With dry_run=True, transcribe + print but file nothing."""
    service = build_drive_service()
    gemini = build_gemini_client()
    session = None if dry_run else _gh_session()

    seen = load_seen()
    pdfs = list_pdfs(service)
    new_pdfs = [f for f in pdfs if f["id"] not in seen]

    if not new_pdfs:
        _log("✨ No new Supernote PDFs. Nothing to do.")
        return 0

    _log(f"📄 {len(new_pdfs)} new PDF(s) to process"
         f"{' (DRY RUN — no issues will be filed)' if dry_run else ''}.")

    filed_total = 0
    for f in new_pdfs:
        file_id, name = f["id"], f["name"]
        _log(f"\n── {name} (id={file_id}) ──")
        try:
            pdf_bytes = download_pdf(service, file_id)
            pages = render_pages(pdf_bytes)
        except Exception as e:
            _log(f"  [ERROR] Could not download/render {name}: {e}. Skipping.")
            continue

        filed_for_file = []
        for page_num, png in enumerate(pages, start=1):
            try:
                note = transcribe_page(gemini, png)
            except Exception as e:
                _log(f"  [ERROR] Gemini failed on page {page_num}: {e}. Skipping page.")
                continue

            tag = note.get("tag", "")
            repo = resolve_repo(tag)
            if not repo:
                _log(f"  page {page_num}: tag={tag!r} → no repo match. Skipping (not filed).")
                continue

            title = (note.get("title") or "").strip() or f"Supernote note: {name} p{page_num}"
            body = _issue_body(note, name, page_num)

            if dry_run:
                _log(f"  page {page_num}: WOULD file in {repo}: {title!r}")
                _log("    ---- issue body preview ----")
                for line in body.splitlines():
                    _log(f"    {line}")
                _log("    ----------------------------")
                filed_for_file.append(repo)
            else:
                try:
                    url = create_issue(session, repo, title, body)
                    _log(f"  page {page_num}: ✅ filed in {repo} → {url}")
                    filed_for_file.append(repo)
                    filed_total += 1
                except Exception as e:
                    _log(f"  page {page_num}: [ERROR] {e}")

        # Only mark a file seen on a real run, so a dry-run doesn't suppress it.
        if not dry_run:
            seen[file_id] = {
                "name": name,
                "filed_at": datetime.now(timezone.utc).isoformat(),
                "repos": filed_for_file,
            }
            save_seen(seen)

    if dry_run:
        _log("\n✅ Dry run complete. No issues were created, no state was written.")
    else:
        _log(f"\n✅ Done. Filed {filed_total} issue(s). State saved to {SEEN_STATE_FILE.name}.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read Supernote PDFs from Google Drive and file GitHub issues by margin tag.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Modes:\n"
            "  --check     verify Drive auth + list the folder (no AI, no issues)\n"
            "  --dry-run   transcribe and print intended issues (no creation)\n"
            "  (default)   transcribe and create GitHub issues\n\n"
            "Required for a full run: GOOGLE_APPLICATION_CREDENTIALS (or\n"
            "./service_account.json), GEMINI_API_KEY, GH_PAT (cross-repo, `repo` scope).\n"
            "Share the Drive folder with the service account's client_email first."
        ),
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true",
                       help="Verify Drive auth and list the folder, then exit.")
    group.add_argument("--dry-run", action="store_true",
                       help="Transcribe and print intended issues without creating them.")
    args = parser.parse_args()

    if args.check:
        return cmd_check()
    return run_pipeline(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())

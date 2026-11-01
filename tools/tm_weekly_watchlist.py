"""Build the VIP 📋╏weekly-watchlist forum in Trader Matrix, posting as Arya.

One forum post per options week (Sat -> Fri expiry), named "w/e MM/DD".
A locked, pinned "What this is" post is the channel's only sticky.
Weekly board content lives in data/watchlists/<month>/board_*.json.

    python tools/tm_weekly_watchlist.py setup            # channel + pinned post + 4 week posts
    python tools/tm_weekly_watchlist.py dev              # mirror to thetadaddies-dev (pinned + this week)
    python tools/tm_weekly_watchlist.py board <thread_id> data/watchlists/2026-11/board_1106.json

IDs land in data/watchlists/discord_ids.json. Token: ~/.config/td/.env (Arya).
"""
import json, sys, time
from pathlib import Path
import urllib.request, urllib.error, urllib.parse

GUILD = "1480917210313789482"          # Trader Matrix
DISCUSSION = "1522279010862629085"     # 🦜 Discussion category
VIP_CHAT = "1481482953727938702"
ROLES = {
    "everyone": "1480917210313789482",
    "free": "1481686538780938290",
    "premium_paid": "1539090564052549714",
    "premium": "1541834015630168136",
    "analyst": "1504641702663815188",
}
IDS_FILE = Path(__file__).resolve().parent.parent / "data/watchlists/discord_ids.json"

VIEW, SEND, EMBED, ATTACH, HISTORY = 1 << 10, 1 << 11, 1 << 14, 1 << 15, 1 << 16
REACT, PUB_THREADS, SEND_IN_THREADS = 1 << 6, 1 << 35, 1 << 38
MEMBER_ALLOW = VIEW | HISTORY | REACT | SEND_IN_THREADS | EMBED | ATTACH
MEMBER_DENY = SEND | PUB_THREADS   # in a forum, SEND = "create posts"


def token():
    for line in Path.home().joinpath(".config/td/.env").read_text().splitlines():
        if line.startswith("DISCORD_BOT_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("no DISCORD_BOT_TOKEN")


def api(method, path, body=None):
    url = f"https://discord.com/api/v10{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bot {token()}", "Content-Type": "application/json",
        "User-Agent": "DiscordBot (mphinance, 1.0)"})
    for _ in range(5):
        try:
            with urllib.request.urlopen(req) as r:
                raw = r.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(json.loads(e.read()).get("retry_after", 1) + 0.2)
                continue
            raise SystemExit(f"{method} {path} -> {e.code}: {e.read().decode()[:400]}")
    raise SystemExit(f"{method} {path}: rate limited")


def ids():
    return json.loads(IDS_FILE.read_text()) if IDS_FILE.exists() else {}


def save(d):
    IDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    IDS_FILE.write_text(json.dumps(d, indent=2) + "\n")


PINNED = """**📋 Weekly Watchlist**
One thread per options week, Saturday through Friday expiration. Each thread is named for the Friday it ends on (w/e 11/06).

**This is the community's watchlist.** Michael seeds each week Sunday night with a few names. After that it's everyone's: add the names you're watching, take notes, vote.
Every name gets a card: the setup, the trigger, where it's wrong. **Nothing is a buy on sight.** Each card says what has to happen first.

**How to join in** (inside the week's thread)
👍 like it · 👎 pass · 👀 watching, react on each card
Reply to a card with your notes or charts
Add a name: `$TICKER` + trigger + where it's wrong (+ a chart if you've got one)

**Tags:** This week · Upcoming · Closed
Sizes are in R. 1R = what you're willing to lose on one trade.

-# VIP only. Watchlist ideas, not trade signals. Not financial advice."""

TOPIC = ("The community watchlist. One thread per options week (Sat to Fri expiry). Add names with "
         "$TICKER + trigger + where it's wrong, react 👍 👎 👀 on every card, reply with notes.")

WEEKS = [  # created newest-first so w/e 11/06 sorts on top (sort = creation date)
    ("w/e 11/27", "Upcoming", "**Week ending Fri 11/27** · Michael seeds it Sun 11/22\n\n"
     "Heads up: market closed Thu 11/26 (Thanksgiving), early close Fri 11/27. AWS re:Invent starts Mon 11/30.\n\n"
     "Add names any time: `$TICKER` + trigger + where it's wrong."),
    ("w/e 11/20", "Upcoming", "**Week ending Fri 11/20** · Michael seeds it Sun 11/15\n\n"
     "Heads up: monthly options expiration Fri 11/20. NVDA reports Tue 11/17 after the close. "
     "The NFLX and PYPL triggers expire this week.\n\n"
     "Add names any time: `$TICKER` + trigger + where it's wrong."),
    ("w/e 11/13", "Upcoming", "**Week ending Fri 11/13** · Michael seeds it Sun 11/08\n\n"
     "Carryover: anything still live from w/e 11/06 rolls in here.\n\n"
     "Add names any time: `$TICKER` + trigger + where it's wrong."),
    ("w/e 11/06", "This week", None),  # opener comes from the board file
]


def setup(board_file):
    d = ids()
    if "forum" not in d:
        vip_pos = api("GET", f"/channels/{VIP_CHAT}")["position"]
        ch = api("POST", f"/guilds/{GUILD}/channels", {
            "name": "📋╏weekly-watchlist", "type": 15, "parent_id": DISCUSSION,
            "topic": TOPIC, "default_sort_order": 1, "default_forum_layout": 1,
            "default_auto_archive_duration": 10080,
            "available_tags": [{"name": "This week", "emoji_name": "🟢"},
                               {"name": "Upcoming", "emoji_name": "🗓️"},
                               {"name": "Closed", "emoji_name": "🔒"}],
            "permission_overwrites": [
                {"id": ROLES["everyone"], "type": 0, "allow": "0", "deny": str(VIEW)},
                {"id": ROLES["free"], "type": 0, "allow": "0", "deny": str(VIEW)},
                *[{"id": ROLES[r], "type": 0, "allow": str(MEMBER_ALLOW), "deny": str(MEMBER_DENY)}
                  for r in ("premium_paid", "premium", "analyst")],
            ]})
        d["forum"] = ch["id"]
        d["tags"] = {t["name"]: t["id"] for t in ch["available_tags"]}
        save(d)
        api("PATCH", f"/guilds/{GUILD}/channels", [{"id": ch["id"], "position": vip_pos + 1,
                                                   "parent_id": DISCUSSION}])
    board = json.loads(Path(board_file).read_text())
    d.setdefault("weeks", {})
    for name, tag, content in WEEKS:
        if name in d["weeks"]:
            continue
        t = api("POST", f"/channels/{d['forum']}/threads", {
            "name": name, "auto_archive_duration": 10080, "applied_tags": [d["tags"][tag]],
            "message": {"content": content or board["opener"]}})
        d["weeks"][name] = t["id"]
        save(d)
        time.sleep(1)
    if "pinned" not in d:
        t = api("POST", f"/channels/{d['forum']}/threads", {
            "name": "📌 What this is", "auto_archive_duration": 10080,
            "message": {"content": PINNED}})
        api("PATCH", f"/channels/{t['id']}", {"flags": 2, "locked": True})
        d["pinned"] = t["id"]
        save(d)
    post_board(d["weeks"]["w/e 11/06"], board_file)
    print(json.dumps(d, indent=2))


def post_board(thread_id, board_file):
    """Post one card per ticker into a week's thread and seed the vote reactions."""
    board = json.loads(Path(board_file).read_text())
    d = ids()
    posted = d.setdefault("cards", {}).setdefault(thread_id, {})
    for card in board["cards"]:
        if card["ticker"] in posted:
            continue
        m = api("POST", f"/channels/{thread_id}/messages", {
            "content": card["text"] + "\n-# Watchlist idea, not a trade signal. Not financial advice.",
            "allowed_mentions": {"parse": []}})
        for e in ("👍", "👎", "👀"):
            api("PUT", f"/channels/{thread_id}/messages/{m['id']}/reactions/{urllib.parse.quote(e)}/@me")
            time.sleep(0.4)
        posted[card["ticker"]] = m["id"]
        save(d)


DEV_GUILD = "1558965355471183954"      # thetadaddies-dev: mph's sandbox for testing ideas
DEV_CATEGORY = "1558965356264038452"   # Text Channels
DEV_NOTE = ("**Why this is here:** this server is the sandbox for testing ideas before they go anywhere "
            "real. This channel is a copy of the VIP weekly watchlist in Trader Matrix, so you can see "
            "how the format works. Poke at it, vote, add names. Break it.\n\n")


def mirror_dev(board_file):
    """Copy the forum to the dev server: open to everyone, pinned post + this week's thread only."""
    d = ids()
    dev = d.setdefault("dev", {})
    if "forum" not in dev:
        ch = api("POST", f"/guilds/{DEV_GUILD}/channels", {
            "name": "📋╏weekly-watchlist", "type": 15, "parent_id": DEV_CATEGORY,
            "topic": TOPIC, "default_sort_order": 1, "default_forum_layout": 1,
            "default_auto_archive_duration": 10080,
            "available_tags": [{"name": "This week", "emoji_name": "🟢"},
                               {"name": "Upcoming", "emoji_name": "🗓️"},
                               {"name": "Closed", "emoji_name": "🔒"}],
            "permission_overwrites": [{"id": DEV_GUILD, "type": 0,
                                       "allow": str(MEMBER_ALLOW), "deny": str(MEMBER_DENY)}]})
        dev["forum"] = ch["id"]
        dev["tags"] = {t["name"]: t["id"] for t in ch["available_tags"]}
        save(d)
    board = json.loads(Path(board_file).read_text())
    dev.setdefault("weeks", {})
    if board["week"] not in dev["weeks"]:
        t = api("POST", f"/channels/{dev['forum']}/threads", {
            "name": board["week"], "auto_archive_duration": 10080,
            "applied_tags": [dev["tags"]["This week"]], "message": {"content": board["opener"]}})
        dev["weeks"][board["week"]] = t["id"]
        save(d)
    if "pinned" not in dev:
        t = api("POST", f"/channels/{dev['forum']}/threads", {
            "name": "📌 What this is", "auto_archive_duration": 10080,
            "message": {"content": PINNED.replace("**📋 Weekly Watchlist**\n",
                                                  "**📋 Weekly Watchlist**\n" + DEV_NOTE)}})
        api("PATCH", f"/channels/{t['id']}", {"flags": 2, "locked": True})
        dev["pinned"] = t["id"]
        save(d)
    post_board(dev["weeks"][board["week"]], board_file)
    print(json.dumps(ids()["dev"], indent=2))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "dev":
        mirror_dev(sys.argv[2] if len(sys.argv) > 2 else
                   str(IDS_FILE.parent / "2026-11/board_1106.json"))
    elif cmd == "setup":
        setup(sys.argv[2] if len(sys.argv) > 2 else
              str(IDS_FILE.parent / "2026-11/board_1106.json"))
    elif cmd == "board":
        post_board(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)

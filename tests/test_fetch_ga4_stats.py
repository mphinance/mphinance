"""Tests for dossier.fetch_ga4_stats credential-source selection.

These exercise the pure _credential_source() priority logic only — no Google
client libraries are imported (the real auth imports are lazy), so this runs
headless in CI.
"""

from dossier import fetch_ga4_stats as g

NO_FILES = {"token_file": "/nonexistent/token.json", "client_file": "/nonexistent/client.json"}


def test_service_account_json_wins():
    assert g._credential_source({"GA4_SERVICE_ACCOUNT_JSON": "{}"}, **NO_FILES) == "service_account_json"


def test_service_account_file():
    assert g._credential_source({"GA4_SERVICE_ACCOUNT_FILE": "/key.json"}, **NO_FILES) == "service_account_file"


def test_refresh_token_requires_all_three():
    full = {"GA4_REFRESH_TOKEN": "r", "GA4_CLIENT_ID": "i", "GA4_CLIENT_SECRET": "s"}
    assert g._credential_source(full, **NO_FILES) == "refresh_token"
    # missing any one → not refresh_token
    assert g._credential_source({"GA4_REFRESH_TOKEN": "r"}, **NO_FILES) == "none"


def test_service_account_beats_refresh_token():
    env = {"GA4_SERVICE_ACCOUNT_JSON": "{}", "GA4_REFRESH_TOKEN": "r",
           "GA4_CLIENT_ID": "i", "GA4_CLIENT_SECRET": "s"}
    assert g._credential_source(env, **NO_FILES) == "service_account_json"


def test_cached_token_when_file_present(tmp_path):
    tf = tmp_path / "token.json"
    tf.write_text("{}")
    assert g._credential_source({}, token_file=str(tf), client_file="/nonexistent") == "cached_token"


def test_interactive_when_only_client_file(tmp_path):
    cf = tmp_path / "client.json"
    cf.write_text("{}")
    assert g._credential_source({}, token_file="/nonexistent", client_file=str(cf)) == "interactive"


def test_env_creds_beat_local_files(tmp_path):
    # env-based (CI) credentials take priority over any local files
    tf = tmp_path / "token.json"
    tf.write_text("{}")
    env = {"GA4_REFRESH_TOKEN": "r", "GA4_CLIENT_ID": "i", "GA4_CLIENT_SECRET": "s"}
    assert g._credential_source(env, token_file=str(tf), client_file=str(tf)) == "refresh_token"


def test_none_when_nothing_available():
    assert g._credential_source({}, **NO_FILES) == "none"

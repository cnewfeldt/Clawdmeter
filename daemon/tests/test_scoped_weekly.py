"""scoped_weekly_fields: model-scoped weekly limit ("Current week (Fable)") from
/api/oauth/usage → wm/wmr/wmn payload fields. Both daemons carry the same helper."""
import datetime
import json
from pathlib import Path

import pytest

from daemon import claude_usage_daemon as mac
from daemon import claude_usage_daemon_windows as win

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "oauth_usage_fable.json").read_text())
# 10 hours before the scoped reset in the fixture
NOW = datetime.datetime.fromisoformat("2026-09-16T19:00:00+00:00").timestamp()


@pytest.mark.parametrize("mod", [mac, win], ids=["macos", "windows"])
def test_extracts_fable_week(mod):
    out = mod.scoped_weekly_fields(FIXTURE, NOW)
    assert out == {"wm": 24, "wmr": 600, "wmn": "Fable"}


@pytest.mark.parametrize("mod", [mac, win], ids=["macos", "windows"])
def test_no_scoped_limit_yields_empty(mod):
    usage = {"limits": [l for l in FIXTURE["limits"] if l["kind"] != "weekly_scoped"]}
    assert mod.scoped_weekly_fields(usage, NOW) == {}
    assert mod.scoped_weekly_fields({}, NOW) == {}
    assert mod.scoped_weekly_fields({"limits": None}, NOW) == {}


@pytest.mark.parametrize("mod", [mac, win], ids=["macos", "windows"])
def test_past_reset_clamps_to_zero_and_missing_name_falls_back(mod):
    lim = {"kind": "weekly_scoped", "percent": 80.4,
           "resets_at": "2026-09-16T18:00:00+00:00", "scope": {"model": None, "surface": None}}
    assert mod.scoped_weekly_fields({"limits": [lim]}, NOW) == {"wm": 80, "wmr": 0, "wmn": "Model"}


@pytest.mark.parametrize("mod", [mac, win], ids=["macos", "windows"])
def test_null_percent_is_skipped(mod):
    lim = {"kind": "weekly_scoped", "percent": None, "resets_at": None, "scope": {}}
    assert mod.scoped_weekly_fields({"limits": [lim]}, NOW) == {}

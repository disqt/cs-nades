import os
import pytest
from scrape_nades import parse_vtt, extract_nade_from_html


def test_parse_vtt_basic():
    vtt = (
        'WEBVTT\\n\\n'
        '1\\n00:00:00.500 --> 00:00:02.500\\n<b>Stand in corner</b>\\n\\n'
        '2\\n00:00:04.016 --> 00:00:06.266\\n<b>Aim at bottom left of window</b>\\n\\n'
        '3\\n00:00:07.150 --> 00:00:09.150\\n<b>Left click throw</b>\\n\\n'
    )
    cues = parse_vtt(vtt)
    assert len(cues) == 3
    assert cues[0] == (0.5, 2.5, "Stand in corner")
    assert cues[1] == (4.016, 6.266, "Aim at bottom left of window")
    assert cues[2] == (7.15, 9.15, "Left click throw")


def test_parse_vtt_strips_html():
    vtt = 'WEBVTT\\n\\n1\\n00:00:01.000 --> 00:00:03.000\\n<b>Walk to <i>spot</i></b>\\n\\n'
    cues = parse_vtt(vtt)
    assert cues[0][2] == "Walk to spot"


def test_parse_vtt_empty():
    assert parse_vtt("WEBVTT\\n\\n") == []
    assert parse_vtt("") == []


def test_extract_nade_from_detail_page():
    fixture = os.path.join(os.path.dirname(__file__), "test_fixture_detail.html")
    if not os.path.exists(fixture):
        pytest.skip("fixture not available")
    with open(fixture, encoding="utf-8") as f:
        html = f.read()
    nade = extract_nade_from_html(html)

    assert nade is not None
    assert nade["slug"] == "ticket-booth-from-tetris"
    assert nade["map"] == "mirage"
    assert nade["team"] == "t"
    assert nade["type"] == "smoke"
    assert nade["titleFrom"] == "Tetris"
    assert nade["titleTo"] == "Ticket Booth"
    assert nade["technique"] == "left_jump"
    assert nade["movement"] == "stationary"
    assert "setpos" in nade["console"]
    assert len(nade["vtt_cues"]) >= 2
    assert nade["asset_id"] == "mirage-smoke-EHvVQ0Ebqm"

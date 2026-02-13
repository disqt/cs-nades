import os
import re
import shutil
import subprocess
import pytest
from scrape_nades import (
    parse_vtt,
    extract_nade_from_html,
    extract_recommended_slugs,
    extract_beginner_smoke_slugs,
    generate_thumbnail,
    extract_result_clip,
)


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


def test_extract_recommended_slugs():
    fixture = os.path.join(os.path.dirname(__file__), "test_fixture_list.html")
    if not os.path.exists(fixture):
        pytest.skip("fixture not available")
    with open(fixture, encoding="utf-8") as f:
        html = f.read()

    slugs = extract_recommended_slugs(html, "mirage")

    assert len(slugs) >= 10, f"Expected at least 10 slugs, got {len(slugs)}"
    assert "top-mid-from-t-spawn" in slugs
    for slug in slugs:
        assert re.match(r"^[a-z0-9-]+$", slug), f"Invalid slug format: {slug!r}"
    assert len(slugs) == len(set(slugs)), "Slugs should be unique"
    assert "mirage" not in slugs


def test_extract_beginner_smoke_slugs():
    fixture = os.path.join(os.path.dirname(__file__), "test_fixture_list.html")
    if not os.path.exists(fixture):
        pytest.skip("fixture not available")
    with open(fixture, encoding="utf-8") as f:
        html = f.read()

    slugs = extract_beginner_smoke_slugs(html)

    # Should find ~10-20 beginner-recommended nades (13 for mirage)
    assert 8 <= len(slugs) <= 25, f"Expected 8-25 beginner slugs, got {len(slugs)}"
    assert "top-mid-from-t-spawn" in slugs
    assert len(slugs) == len(set(slugs)), "Slugs should be unique"
    # Much fewer than total nades on the page
    all_slugs = extract_recommended_slugs(html, "mirage")
    assert len(slugs) < len(all_slugs), "Beginner subset should be smaller than all nades"


def test_generate_thumbnail(tmp_path):
    """Test thumbnail generation with ffmpeg."""
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not available")

    # Create a test image using ffmpeg (generate a solid color frame)
    test_img = tmp_path / "test.jpg"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=red:s=800x450:d=1",
        "-frames:v", "1", "-q:v", "2", str(test_img)
    ], capture_output=True, check=True)

    thumb = generate_thumbnail(str(test_img), 400)
    assert os.path.exists(thumb)
    assert "_thumb" in thumb
    assert thumb.endswith(".jpg")


def test_extract_result_clip(tmp_path):
    """Test result clip extraction with ffmpeg."""
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not available")

    # Create a 6-second test video
    test_video = tmp_path / "test_video.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=blue:s=640x360:d=6",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        str(test_video)
    ], capture_output=True, check=True)

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    extract_result_clip(str(test_video), 3.0, str(output_dir))

    assert (output_dir / "result.mp4").exists()
    assert (output_dir / "result_thumb.mp4").exists()
    # Thumbnail should be smaller than full resolution
    full_size = (output_dir / "result.mp4").stat().st_size
    thumb_size = (output_dir / "result_thumb.mp4").stat().st_size
    assert thumb_size < full_size

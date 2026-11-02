"""Tests for M-067 — Binary and asset awareness.

TIER: integration

Images, archives, and large files are described, never
dumped into context: images from their headers only
(PNG, GIF, JPEG, BMP, WebP, ICO, TIFF, SVG — stdlib
parsers over a bounded header read), archives from
their member listings (zip and tar via the stdlib
readers, the listing capped and named; a plain gzip
stream from its header name and trailer size; 7z and
RAR honestly unlistable on this road), large files by
size and sniffed kind. Every asset carries the role
the map notes for it, inferred from its kind and path
by named rules with the rule recorded as evidence.
Every test builds a real fixture tree on disk.
"""

from __future__ import annotations

import gzip
import io
import struct
import tarfile
import zipfile
import zlib
from pathlib import Path

import pytest

from mythic_agent.tools import asset_sight as asx
from mythic_agent.tools.asset_sight import (
    ASSET_SLICE,
    LARGE_FILE_BYTES,
    PLAIN_EXPLANATION,
    USAGE,
    asset_role,
    asset_sight,
    classify_asset,
    describe_image,
    find_asset_files,
    format_asset_report,
    list_archive,
    parse_assets_args,
    render_markdown,
    sniff_image,
)

SECRET = "MEMBER-CONTENT-THAT-MUST-NEVER-BE-DUMPED"


def _png_bytes(width: int, height: int) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data)
                              & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + b"\x01\x02\x03" * width
                   for _ in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b""))


def _gif_bytes(width: int, height: int) -> bytes:
    return b"GIF89a" + struct.pack("<HH", width, height) + b"\x00" * 16


def _jpeg_bytes(width: int, height: int) -> bytes:
    app0 = b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00" + b"\x00" * 9
    sof = (b"\xff\xc0" + struct.pack(">H", 17) + b"\x08"
           + struct.pack(">HH", height, width) + b"\x03"
           + b"\x01\x22\x00\x02\x11\x01\x03\x11\x01")
    return b"\xff\xd8" + app0 + sof + b"\xff\xd9"


def _bmp_bytes(width: int, height: int) -> bytes:
    dib = struct.pack("<IiiHH", 40, width, height, 1, 24) + b"\x00" * 24
    return b"BM" + struct.pack("<IHHI", 54, 0, 0, 54) + dib


def _webp_bytes(width: int, height: int) -> bytes:
    vp8x = (b"VP8X" + struct.pack("<I", 10) + b"\x00" * 4
            + (width - 1).to_bytes(3, "little")
            + (height - 1).to_bytes(3, "little"))
    return b"RIFF" + struct.pack("<I", 4 + len(vp8x)) + b"WEBP" + vp8x


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "banner.png").write_bytes(_png_bytes(800, 200))
    (tmp_path / "anim.gif").write_bytes(_gif_bytes(64, 48))
    (tmp_path / "photo.jpg").write_bytes(_jpeg_bytes(1024, 768))
    (tmp_path / "icon.bmp").write_bytes(_bmp_bytes(32, 32))
    (tmp_path / "hero.webp").write_bytes(_webp_bytes(1200, 630))
    (tmp_path / "logo.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="240" '
        'height="80"><rect width="240" height="80"/></svg>',
        encoding="utf-8")
    with zipfile.ZipFile(tmp_path / "bundle.zip", "w") as zf:
        zf.writestr("inner/a.txt", "alpha")
        zf.writestr("inner/b.bin", SECRET)
    tar_path = tmp_path / "pack.tar"
    with tarfile.open(tar_path, "w") as tf:
        for name, body in (("one.py", b"print(1)\n"),
                           ("two.py", b"print(2)\n")):
            entry = tarfile.TarInfo(name)
            entry.size = len(body)
            tf.addfile(entry, io.BytesIO(body))
    with gzip.open(tmp_path / "notes.txt.gz", "wb") as handle:
        handle.write(b"field notes\n" * 10)
    (tmp_path / "code.py").write_text("print('code')\n",
                                      encoding="utf-8")
    return tmp_path


# -- recognition ------------------------------------------------------------------------

def test_classify_by_magic_extension_and_size(tmp_path: Path):
    png = tmp_path / "x.bin"
    head = _png_bytes(4, 4)
    assert classify_asset(png, len(head), head) == "image"
    zip_head = b"PK\x03\x04" + b"\x00" * 32
    assert classify_asset(tmp_path / "x.dat", 100, zip_head) == "archive"
    plain = tmp_path / "big.log"
    assert classify_asset(
        plain, LARGE_FILE_BYTES, b"plain text\n") == "large"
    assert classify_asset(
        plain, 12, b"plain text\n") == ""
    assert sniff_image(b"<svg xmlns='x'></svg>") == "svg"


def test_find_asset_files_skips_vcs_and_code(project: Path):
    found, warnings = find_asset_files(project)
    names = {p.name for p in found}
    assert {"banner.png", "anim.gif", "photo.jpg", "icon.bmp",
            "hero.webp", "logo.svg", "bundle.zip", "pack.tar",
            "notes.txt.gz"} <= names
    assert "code.py" not in names
    assert warnings == []
    git_dir = project / ".git"
    git_dir.mkdir()
    (git_dir / "hidden.png").write_bytes(_png_bytes(2, 2))
    found, _ = find_asset_files(project)
    assert "hidden.png" not in {p.name for p in found}


# -- image headers ------------------------------------------------------------------------

def test_png_gif_jpeg_bmp_webp_dimensions(project: Path):
    report = asset_sight(project, "images")
    by_name = {f.path.split("/")[-1]: f for f in report.files}
    assert by_name["banner.png"].image.dimensions() == "800x200"
    assert by_name["banner.png"].image.format == "png"
    assert by_name["anim.gif"].image.dimensions() == "64x48"
    assert by_name["photo.jpg"].image.dimensions() == "1024x768"
    assert by_name["photo.jpg"].image.detail == "3 component(s)"
    assert by_name["icon.bmp"].image.dimensions() == "32x32"
    assert by_name["hero.webp"].image.dimensions() == "1200x630"


def test_svg_declared_size_and_viewbox(tmp_path: Path):
    sized = tmp_path / "a.svg"
    sized.write_text('<svg width="10" height="20"></svg>',
                     encoding="utf-8")
    info = describe_image(sized.read_bytes())
    assert (info.format, info.width, info.height) == ("svg", 10, 20)
    boxed = tmp_path / "b.svg"
    boxed.write_text('<svg viewBox="0 0 300 150"></svg>',
                     encoding="utf-8")
    info = describe_image(boxed.read_bytes())
    assert (info.width, info.height, info.detail) == (300, 150, "viewBox")


def test_broken_image_header_is_named(tmp_path: Path):
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"\x89PNG\r\n\x1a\n")  # signature only
    report = asset_sight(tmp_path)
    entry = report.files[0]
    assert entry.kind == "image"
    assert entry.image.width == 0
    assert "did not yield dimensions" in entry.note


# -- archive listings ---------------------------------------------------------------------

def test_zip_listing_names_and_sizes(project: Path):
    info = list_archive(project / "bundle.zip")
    assert info.format == "zip"
    assert info.member_count == 2
    assert info.member_names() == ("inner/a.txt", "inner/b.bin")
    assert info.members[0].size == 5


def test_zip_member_content_is_never_dumped(project: Path):
    report = asset_sight(project)
    blob = str(report.record()) + format_asset_report(
        {"report": report.record(),
         "plain_explanation": PLAIN_EXPLANATION}) \
        + render_markdown(report)
    assert SECRET not in blob


def test_tar_and_gzip_accounts(project: Path):
    tar = list_archive(project / "pack.tar")
    assert tar.format == "tar"
    assert tar.member_names() == ("one.py", "two.py")
    gz = list_archive(project / "notes.txt.gz")
    assert gz.format == "gzip"
    assert gz.member_count == 1
    assert gz.total_size == len(b"field notes\n" * 10)
    assert "not decompressed" in gz.note


def test_tar_gz_is_a_tar_listing(tmp_path: Path):
    path = tmp_path / "snap.tar.gz"
    with tarfile.open(path, "w:gz") as tf:
        entry = tarfile.TarInfo("inside.py")
        body = b"x = 1\n"
        entry.size = len(body)
        tf.addfile(entry, io.BytesIO(body))
    info = list_archive(path)
    assert info.format == "tar"
    assert info.member_names() == ("inside.py",)


def test_unlistable_formats_are_honest(tmp_path: Path):
    seven = tmp_path / "vault.7z"
    seven.write_bytes(b"7z\xbc\xaf'\x1c" + b"\x00" * 64)
    info = list_archive(seven)
    assert info.format == "7z"
    assert info.members == []
    assert "unavailable on this road" in info.note


def test_corrupt_zip_is_named(tmp_path: Path):
    bad = tmp_path / "bad.zip"
    bad.write_bytes(b"PK\x03\x04" + b"garbage" * 16)
    info = list_archive(bad)
    assert info.members == []
    assert "could not be read" in info.note


def test_member_listing_cap_is_named(tmp_path: Path):
    path = tmp_path / "many.zip"
    with zipfile.ZipFile(path, "w") as zf:
        for index in range(105):
            zf.writestr(f"m{index:03d}.txt", "x")
    info = list_archive(path)
    assert info.member_count == 105
    assert len(info.members) == asx.MAX_MEMBERS_LISTED
    assert "capped" in info.note


# -- large files --------------------------------------------------------------------------

def test_large_text_file_lines_counted_not_dumped(tmp_path: Path):
    big = tmp_path / "big.log"
    line = "ordinary log line\n"
    repeats = LARGE_FILE_BYTES // len(line) + 10
    big.write_text(line * repeats + "UNIQUE-TAIL-LINE\n",
                   encoding="utf-8")
    report = asset_sight(tmp_path)
    entry = report.files[0]
    assert entry.kind == "large" and entry.large is True
    assert entry.lines == repeats + 1
    assert "UNIQUE-TAIL-LINE" not in format_asset_report(
        {"report": report.record(),
         "plain_explanation": PLAIN_EXPLANATION})


def test_large_binary_described_by_size(tmp_path: Path):
    blob = tmp_path / "blob.bin"
    blob.write_bytes(b"\x00\x01" + b"\x07" * LARGE_FILE_BYTES)
    report = asset_sight(tmp_path)
    entry = report.files[0]
    assert entry.kind == "large"
    assert entry.size_bytes == LARGE_FILE_BYTES + 2
    assert "described by size alone" in entry.note


# -- roles ----------------------------------------------------------------------------------

def test_roles_follow_the_named_rules(project: Path):
    report = asset_sight(project)
    by_name = {f.path.split("/")[-1]: f for f in report.files}
    assert by_name["banner.png"].role == "documentation asset"
    assert by_name["anim.gif"].role == "image asset"
    assert "role from its kind" in by_name["anim.gif"].role_evidence
    role, evidence = asset_role("tests/fixtures/pack.zip", "archive")
    assert role == "test fixture"
    role, _ = asset_role("data/table.csv", "large")
    assert role == "data file"
    role, _ = asset_role("nightly-backup.zip", "archive")
    assert role == "backup or snapshot archive"
    role, _ = asset_role("static/hero.png", "image")
    assert role == "project asset"


# -- the report -----------------------------------------------------------------------------

def test_show_report_counts_and_modes(project: Path):
    report = asset_sight(project)
    n_files, n_images, n_archives, n_large = report.totals()
    assert (n_files, n_images, n_archives, n_large) == (9, 6, 3, 0)
    images = asset_sight(project, "images")
    assert {f.kind for f in images.files} == {"image"}
    archives = asset_sight(project, "archives")
    assert {f.kind for f in archives.files} == {"archive"}
    large = asset_sight(project, "large")
    assert large.files == []


def test_file_mode_and_errors(project: Path):
    one = asset_sight(project, "file", target="docs/banner.png")
    assert one.files[0].path == "docs/banner.png"
    missing = asset_sight(project, "file", target="nope.png")
    assert missing.status == "error"
    plain = asset_sight(project, "file", target="code.py")
    assert plain.status == "error"
    assert "not an asset" in plain.note


def test_disabled_reads_nothing(project: Path):
    report = asset_sight(project, enabled=False)
    assert report.status == "disabled"
    assert report.files == []


def test_missing_workspace_is_an_error(tmp_path: Path):
    report = asset_sight(tmp_path / "absent")
    assert report.status == "error"


def test_empty_workspace_says_so(tmp_path: Path):
    report = asset_sight(tmp_path)
    assert report.status == "ok"
    assert "no asset files" in report.note


def test_parse_assets_args():
    assert parse_assets_args("") == {"action": "show"}
    assert parse_assets_args("images") == {"action": "images"}
    assert parse_assets_args("docs/banner.png") == {
        "action": "file", "target": "docs/banner.png"}
    with pytest.raises(ValueError):
        parse_assets_args("a.png b.png")


def test_format_and_render_use_the_reports_own_values(project: Path):
    report = asset_sight(project)
    text = format_asset_report(
        {"report": report.record(),
         "plain_explanation": PLAIN_EXPLANATION})
    assert "Asset sight (M-067)" in text
    assert "role: documentation asset" in text
    assert "inner/a.txt" in text
    page = render_markdown(report)
    n_files, n_images, n_archives, _ = report.totals()
    assert f"**{n_files} asset(s)**" in page
    assert f"**{n_images} image(s)**" in page
    assert f"**{n_archives} archive(s)**" in page
    assert ASSET_SLICE == "M-067"
    assert USAGE.startswith("Usage")


def test_asset_sight_never_writes(project: Path):
    before = {p: p.read_bytes() for p in project.rglob("*")
              if p.is_file()}
    asset_sight(project)
    asset_sight(project, "file", target="bundle.zip")
    after = {p: p.read_bytes() for p in project.rglob("*")
             if p.is_file()}
    assert before == after


def test_repo_map_never_carries_the_asset_as_code(project: Path):
    # The map-facing half of the slice: the repo map
    # (M-044) must not carry an asset as a code entry;
    # asset sight's role account is what the map notes
    # instead (the map's own skip wording stays pinned
    # by its own slices).
    from mythic_agent.context.repo_map import build_repo_map

    repo_map = build_repo_map(project)
    entry_paths = {entry.path for entry in repo_map.entries}
    assert "docs/banner.png" not in entry_paths
    assert "bundle.zip" not in entry_paths
    report = asset_sight(project)
    roles = {f.path: f.role for f in report.files}
    assert roles["docs/banner.png"] == "documentation asset"


# -- surfaces ---------------------------------------------------------------------------

def _bare_agent(root: Path, config=None):
    from mythic_agent.agents.llm import Agent

    agent = Agent.__new__(Agent)
    agent.project_root = root
    agent.config = config or {}
    agent._session_store = None
    agent.session_id = None
    return agent


def test_agent_surfaces(project: Path):
    agent = _bare_agent(project)
    status = agent.asset_sight()
    assert status["report"]["status"] == "ok"
    assert len(status["report"]["files"]) == 9
    one = agent.asset_sight("file", target="bundle.zip")
    assert one["report"]["files"][0]["kind"] == "archive"


def test_agent_respects_the_config_switch(project: Path):
    agent = _bare_agent(project, {"asset_sight": False})
    status = agent.asset_sight()
    assert status["report"]["status"] == "disabled"
    assert status["report"]["files"] == []


def test_terminal_road(project: Path):
    from mythic_agent.terminal import _slash

    agent = _bare_agent(project)
    handled, _, text = _slash(agent, "/assets")
    assert handled and "Asset sight (M-067)" in text
    handled, _, text = _slash(agent, "/assets archives")
    assert handled and "bundle.zip" in text
    handled, _, text = _slash(agent, "/assets a.png b.png")
    assert handled and "Usage" in text


def test_setting_lives_in_defaults_and_catalogue():
    import yaml

    root = Path(__file__).resolve().parents[1]
    defaults = yaml.safe_load(
        (root / "mythic_agent/data/config_defaults.yaml").read_text(
            encoding="utf-8"))
    assert defaults["asset_sight"] is True
    catalogue = yaml.safe_load(
        (root / "mythic_agent/data/config_catalog.yaml").read_text(
            encoding="utf-8"))
    entries = [s for s in catalogue["settings"]
               if s["name"] == "asset_sight"]
    assert len(entries) == 1
    assert entries[0]["id"] == "S-57"
    assert asx.enabled_from_config({}) is True
    assert asx.enabled_from_config({"asset_sight": False}) is False
    assert asx.enabled_from_config(None) is True


def test_config_catalogue_carries_the_setting():
    from mythic_agent.core.config_catalog import load_catalog

    catalog = load_catalog()
    entry = [s for s in catalog.settings
             if s.name == "asset_sight"]
    assert len(entry) == 1
    assert entry[0].id == "S-57"


def test_gap_audit_has_no_m067_row_recorded():
    # Checked at build time (M-066's pattern): no census
    # gap row is owned by M-067, so no module_kind flip
    # exists to make for this slice.
    import yaml

    root = Path(__file__).resolve().parents[1]
    audit = yaml.safe_load(
        (root / "mythic_agent/data/gap_audit.yaml").read_text(
            encoding="utf-8"))
    assert [r for r in audit["rows"] if r["slice"] == "M-067"] == []

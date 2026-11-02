"""Binary and asset sight (M-067).

Part III — Code Intelligence. The roadmap's words for
this slice: "Binary and asset awareness: images,
archives, and large files are *described, never dumped
into context*; the map notes their roles."

What ships here, in ``mythic_agent/tools/asset_sight.py``:

* **Images are described from their headers only.** A
  bounded header read (never a decode) gives the format
  and dimensions for PNG, GIF, JPEG, BMP, WebP, ICO and
  TIFF, read by small stdlib parsers written here; SVG
  (a text format) gives its declared width/height or
  viewBox from its opening bytes. No pixel data is ever
  read into a report.
* **Archives are described from their listings.** Zip
  and tar archives (including the compressed tar
  family) are listed through the stdlib readers: member
  names, sizes and compressed sizes, the listing capped
  and the cap named. A plain gzip stream is described
  from its header name and its trailer's stored size. 7z
  and RAR have no stdlib reader, so they are described
  from their magic bytes with the member listing
  honestly recorded as unavailable. Nothing is ever
  extracted.
* **Large files are described, not read.** Any file at
  or over :data:`LARGE_FILE_BYTES` that is not already
  an image or an archive is described by its size and
  its sniffed kind; a large text file's lines are
  counted by streaming (content never retained, the
  count capped and the cap named).
* **The map notes their roles.** Every asset carries
  the role it plays in the workspace — documentation
  asset, test fixture, data file, backup or snapshot
  archive, project asset — inferred from its kind and
  path by named rules, with the rule that fired recorded
  as evidence on the asset itself. The repo map
  (M-044) keeps its pinned "binary file" skip for such
  files; this report is the map-facing account of what
  those files are and what they are for, cross-checked
  against the live map in this slice's tests.
* **The surfaces.** ``Agent.asset_sight(...)`` and
  ``/assets [show | <file> | images | archives | large]``
  on the terminal and TUI system-command roads, sharing
  this module's parser and formatter. The setting
  ``asset_sight`` (on by default) closes the road
  plainly.

Honesty rules, pinned by the slice's tests:

* **Described, never dumped.** Reports carry names,
  formats, dimensions, sizes and member listings —
  never file content, pixel data or archive payloads.
* **Headers only, listings only.** An image whose
  header does not parse is reported with that failure,
  never dressed as dimensioned; an archive whose
  listing cannot be read carries its reader's error.
* **Absence and caps are named.** A workspace with no
  assets says so; a capped scan or listing names its
  cap; a role taken from no rule says so plainly.
"""

from __future__ import annotations

__all__ = [
    "PLAIN_EXPLANATION",
    "ASSET_SLICE",
    "USAGE",
    "IMAGE_EXTENSIONS",
    "ARCHIVE_EXTENSIONS",
    "LARGE_FILE_BYTES",
    "HEADER_READ_BYTES",
    "MAX_SCAN_FILES",
    "MAX_MEMBERS_LISTED",
    "ImageInfo",
    "ArchiveMember",
    "ArchiveInfo",
    "AssetFile",
    "AssetReport",
    "enabled_from_config",
    "classify_asset",
    "sniff_image",
    "describe_image",
    "list_archive",
    "asset_role",
    "find_asset_files",
    "describe_asset",
    "asset_sight",
    "parse_assets_args",
    "format_asset_report",
    "render_markdown",
]

import gzip
import re
import struct
import tarfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

ASSET_SLICE = "M-067"

PLAIN_EXPLANATION = (
    "Asset sight describes the workspace's binary and "
    "asset files without ever dumping them into "
    "context: /assets show reads each image's header "
    "for its format and dimensions, lists each "
    "archive's members by name and size, and describes "
    "each large file by size and kind — and notes the "
    "role each file plays in the workspace (a "
    "documentation asset, a test fixture, a data file, "
    "a backup). Nothing is decoded, extracted or "
    "executed on this road."
)

USAGE = "Usage: /assets [show | <file> | images | archives | large]"

IMAGE_EXTENSIONS = (".png", ".gif", ".jpg", ".jpeg", ".bmp",
                    ".webp", ".ico", ".tif", ".tiff", ".svg")
ARCHIVE_EXTENSIONS = (".zip", ".tar", ".tgz", ".tar.gz",
                      ".tar.bz2", ".tbz2", ".tar.xz", ".txz",
                      ".gz", ".bz2", ".xz", ".7z", ".rar")

#: A file at or over this size is a large file.
LARGE_FILE_BYTES = 1_000_000
#: How much of a file's head the sniffers may read.
HEADER_READ_BYTES = 65_536
#: Line counting for a large text file reads at most this far.
LINE_COUNT_CAP_BYTES = 64_000_000

MAX_SCAN_FILES = 500
MAX_MEMBERS_LISTED = 100

_SKIP_DIRS = {".git", ".hg", ".svn", "__pycache__",
              "node_modules", "dist", "build",
              ".venv", ".venv-baseline", "venv"}


def enabled_from_config(config: Optional[Dict[str, Any]]) -> bool:
    """Asset sight is on unless config says so."""
    if not config:
        return True
    return config.get("asset_sight", True) is not False


# ---------------------------------------------------------------------------
# Recognition
# ---------------------------------------------------------------------------

def _magic_image_format(head: bytes) -> str:
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if head.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if head.startswith(b"BM"):
        return "bmp"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    if head[:4] in (b"\x00\x00\x01\x00", b"\x00\x00\x02\x00"):
        return "ico"
    if head[:4] in (b"II*\x00", b"MM\x00*"):
        return "tiff"
    return ""


def _magic_archive_format(head: bytes) -> str:
    if head[:4] in (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"):
        return "zip"
    if head[:3] == b"\x1f\x8b\x08":
        return "gzip"
    if head[:3] == b"BZh":
        return "bzip2"
    if head[:6] == b"\xfd7zXZ\x00":
        return "xz"
    if head[:6] == b"7z\xbc\xaf'\x1c":
        return "7z"
    if head[:7] == b"Rar!\x1a\x07\x00" or head[:8] == b"Rar!\x1a\x07\x01\x00":
        return "rar"
    if head[257:262] == b"ustar":
        return "tar"
    return ""


def sniff_image(head: bytes) -> str:
    """The image format the head bytes prove, or ''."""
    fmt = _magic_image_format(head)
    if fmt:
        return fmt
    stripped = head.lstrip()
    if stripped.startswith(b"<") and b"<svg" in head[:4096]:
        return "svg"
    return ""


def _extension_of(name: str) -> str:
    lower = name.lower()
    for ext in (".tar.gz", ".tar.bz2", ".tar.xz"):
        if lower.endswith(ext):
            return ext
    return Path(lower).suffix


def classify_asset(path: Path, size: int, head: bytes) -> str:
    """The asset kind of one file: image | archive | large | ''.

    Magic bytes win over the file name wherever both
    speak; a large file of no recognised kind is still
    an asset (kind ``large``) once it crosses the
    threshold.
    """
    if sniff_image(head):
        return "image"
    if _magic_archive_format(head):
        return "archive"
    ext = _extension_of(path.name)
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in ARCHIVE_EXTENSIONS:
        return "archive"
    if size >= LARGE_FILE_BYTES:
        return "large"
    return ""


# ---------------------------------------------------------------------------
# Image headers — described, never decoded
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ImageInfo:
    """One image's header account."""

    format: str = ""
    width: int = 0
    height: int = 0
    detail: str = ""

    def dimensions(self) -> str:
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        return "dimensions not in the header read"

    def record(self) -> Dict[str, Any]:
        return {"format": self.format, "width": self.width,
                "height": self.height, "detail": self.detail}


def _jpeg_dimensions(head: bytes) -> Tuple[int, int, str]:
    """Walk JPEG segments for a Start-Of-Frame marker."""
    pos = 2
    while pos + 4 <= len(head):
        if head[pos] != 0xFF:
            pos += 1
            continue
        marker = head[pos + 1]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        length = struct.unpack(">H", head[pos + 2:pos + 4])[0]
        if length < 2:
            break
        if marker in (0xC0, 0xC1, 0xC2):
            if pos + 9 <= len(head):
                height, width = struct.unpack(
                    ">HH", head[pos + 5:pos + 9])
                components = head[pos + 9] if pos + 10 <= len(head) else 0
                return width, height, f"{components} component(s)"
            break
        if marker == 0xDA:  # start of scan: no SOF before it
            break
        pos += 2 + length
    return 0, 0, ""


def _webp_dimensions(head: bytes) -> Tuple[int, int, str]:
    chunk = head[12:16]
    if chunk == b"VP8X" and len(head) >= 30:
        width = int.from_bytes(head[24:27], "little") + 1
        height = int.from_bytes(head[27:30], "little") + 1
        return width, height, "extended (VP8X)"
    if chunk == b"VP8L" and len(head) >= 25:
        bits = int.from_bytes(head[21:25], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1, \
            "lossless (VP8L)"
    if chunk == b"VP8 " and len(head) >= 30:
        width = struct.unpack("<H", head[26:28])[0] & 0x3FFF
        height = struct.unpack("<H", head[28:30])[0] & 0x3FFF
        return width, height, "lossy (VP8)"
    return 0, 0, ""


def _tiff_dimensions(head: bytes) -> Tuple[int, int]:
    endian = "<" if head[:2] == b"II" else ">"
    if len(head) < 8:
        return 0, 0
    ifd_offset = struct.unpack(endian + "I", head[4:8])[0]
    if ifd_offset + 2 > len(head):
        return 0, 0
    count = struct.unpack(
        endian + "H", head[ifd_offset:ifd_offset + 2])[0]
    width = height = 0
    for index in range(count):
        entry = ifd_offset + 2 + index * 12
        if entry + 12 > len(head):
            break
        tag, field_type = struct.unpack(
            endian + "HH", head[entry:entry + 4])
        if tag not in (256, 257):
            continue
        raw = head[entry + 8:entry + 12]
        value = struct.unpack(endian + "H", raw[:2])[0] \
            if field_type == 3 else struct.unpack(endian + "I", raw)[0]
        if tag == 256:
            width = value
        else:
            height = value
    return width, height


_SVG_SIZE_RE = re.compile(
    r"<svg[^>]*\bwidth=[\"'](\d+(?:\.\d+)?)[\"']"
    r"[^>]*\bheight=[\"'](\d+(?:\.\d+)?)[\"']", re.IGNORECASE)
_SVG_VIEWBOX_RE = re.compile(
    r"<svg[^>]*\bviewBox=[\"']([\d\s.,-]+)[\"']", re.IGNORECASE)


def describe_image(head: bytes, fmt: str = "") -> ImageInfo:
    """One image's header account, from its head bytes only.

    A header that does not parse yields an ImageInfo
    carrying the format the magic proved (or the name
    claimed) and zero dimensions — named in ``detail``,
    never dressed as a measured size.
    """
    fmt = fmt or sniff_image(head)
    if fmt == "png" and len(head) >= 26 and head[12:16] == b"IHDR":
        width, height = struct.unpack(">II", head[16:24])
        return ImageInfo(
            "png", width, height,
            f"bit depth {head[24]}, colour type {head[25]}")
    if fmt == "gif" and len(head) >= 10:
        width, height = struct.unpack("<HH", head[6:10])
        version = head[3:6].decode("ascii", "replace")
        return ImageInfo("gif", width, height, f"GIF{version}")
    if fmt == "jpeg":
        width, height, detail = _jpeg_dimensions(head)
        return ImageInfo("jpeg", width, height, detail or
                         "no frame header in the header read")
    if fmt == "bmp" and len(head) >= 26:
        dib = struct.unpack("<I", head[14:18])[0]
        if dib >= 40 and len(head) >= 30:
            width, height = struct.unpack("<ii", head[18:26])
            bpp = struct.unpack("<H", head[28:30])[0]
            return ImageInfo("bmp", abs(width), abs(height),
                             f"{bpp} bits per pixel")
        return ImageInfo("bmp", 0, 0, "core DIB header; "
                         "dimensions not read")
    if fmt == "webp":
        width, height, detail = _webp_dimensions(head)
        return ImageInfo("webp", width, height,
                         detail or "unknown WebP chunk")
    if fmt == "ico" and len(head) >= 8:
        count = struct.unpack("<H", head[4:6])[0]
        width = head[6] or 256
        height = head[7] or 256
        return ImageInfo("ico", width, height,
                         f"{count} image(s) in the icon")
    if fmt == "tiff":
        width, height = _tiff_dimensions(head)
        return ImageInfo("tiff", width, height,
                         "IFD width/height tags")
    if fmt == "svg":
        text = head[:8192].decode("utf-8", "replace")
        match = _SVG_SIZE_RE.search(text)
        if match:
            return ImageInfo("svg", int(float(match.group(1))),
                             int(float(match.group(2))),
                             "declared width/height")
        match = _SVG_VIEWBOX_RE.search(text)
        if match:
            parts = [p for p in re.split(r"[\s,]+",
                                          match.group(1).strip()) if p]
            if len(parts) == 4:
                return ImageInfo(
                    "svg", int(float(parts[2])), int(float(parts[3])),
                    "viewBox")
        return ImageInfo("svg", 0, 0, "no size declared in the "
                         "opening bytes")
    return ImageInfo(fmt, 0, 0, "header not recognised" if not fmt
                     else "header too short or malformed to read")


# ---------------------------------------------------------------------------
# Archive listings — described, never extracted
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ArchiveMember:
    """One archive member's listing account."""

    name: str
    size: int = 0
    compressed: int = 0

    def record(self) -> Dict[str, Any]:
        return {"name": self.name, "size": self.size,
                "compressed": self.compressed}


@dataclass
class ArchiveInfo:
    """One archive's listing account."""

    format: str = ""
    members: List[ArchiveMember] = field(default_factory=list)
    member_count: int = 0
    total_size: int = 0
    note: str = ""

    def member_names(self) -> Tuple[str, ...]:
        return tuple(m.name for m in self.members)

    def record(self) -> Dict[str, Any]:
        return {"format": self.format,
                "members": [m.record() for m in self.members],
                "member_count": self.member_count,
                "total_size": self.total_size,
                "note": self.note}


def _cap_members(info: ArchiveInfo,
                 members: List[ArchiveMember]) -> None:
    info.member_count = len(members)
    info.total_size = sum(m.size for m in members)
    info.members = members[:MAX_MEMBERS_LISTED]
    if len(members) > MAX_MEMBERS_LISTED:
        info.note = (
            f"listing capped at {MAX_MEMBERS_LISTED} of "
            f"{len(members)} member(s); the rest were "
            "counted, not listed")


def _list_zip(path: Path) -> ArchiveInfo:
    info = ArchiveInfo(format="zip")
    try:
        with zipfile.ZipFile(path) as zf:
            members = [
                ArchiveMember(entry.filename, entry.file_size,
                              entry.compress_size)
                for entry in zf.infolist() if not entry.is_dir()]
    except (zipfile.BadZipFile, OSError) as exc:
        info.note = f"the archive listing could not be read: {exc}"
        return info
    _cap_members(info, members)
    return info


def _list_tar(path: Path) -> ArchiveInfo:
    info = ArchiveInfo(format="tar")
    try:
        with tarfile.open(path, "r:*") as tf:
            members = [
                ArchiveMember(entry.name, entry.size, entry.size)
                for entry in tf.getmembers() if entry.isfile()]
    except (tarfile.TarError, OSError, EOFError) as exc:
        info.note = f"the archive listing could not be read: {exc}"
        return info
    _cap_members(info, members)
    return info


def _describe_gzip(path: Path, head: bytes) -> ArchiveInfo:
    """A plain gzip stream: header name + trailer size.

    The stored uncompressed size is the trailer's ISIZE
    (the true size modulo 2**32 — named as such). The
    member listing of a single stream is the stream
    itself; its content is never decompressed here.
    """
    info = ArchiveInfo(format="gzip")
    name = ""
    if len(head) >= 10 and head[3] & 0x08:  # FNAME flag
        end = head.find(b"\x00", 10)
        if end > 10:
            name = head[10:end].decode("utf-8", "replace")
    try:
        with open(path, "rb") as handle:
            handle.seek(-4, 2)
            trailer = handle.read(4)
    except OSError as exc:
        info.note = f"the gzip trailer could not be read: {exc}"
        return info
    if len(trailer) == 4:
        stored = struct.unpack("<I", trailer)[0]
        info.member_count = 1
        info.total_size = stored
        info.members = [ArchiveMember(
            name or "(unnamed gzip stream)", stored, path.stat().st_size)]
        info.note = (
            "single gzip stream; the size is the trailer's "
            "stored value (the true size modulo 2^32); the "
            "content was not decompressed")
    return info


def list_archive(path: Path, fmt: str = "") -> ArchiveInfo:
    """One archive's listing account — nothing extracted.

    Formats with no stdlib reader (7z, RAR) and the
    single-stream compressors (bzip2, xz) are described
    from their magic with the listing honestly recorded
    as unavailable on this road.
    """
    if not fmt:
        try:
            with open(path, "rb") as handle:
                head = handle.read(512)
        except OSError as exc:
            return ArchiveInfo(note=f"the file could not be read: {exc}")
        fmt = _magic_archive_format(head)
        if not fmt:
            ext = _extension_of(path.name)
            fmt = {".zip": "zip", ".tar": "tar", ".tgz": "tar",
                   ".tar.gz": "tar", ".tar.bz2": "tar",
                   ".tbz2": "tar", ".tar.xz": "tar", ".txz": "tar",
                   ".gz": "gzip", ".bz2": "bzip2", ".xz": "xz",
                   ".7z": "7z", ".rar": "rar"}.get(ext, "")
    if fmt == "zip":
        return _list_zip(path)
    if fmt == "tar":
        return _list_tar(path)
    if fmt == "gzip":
        try:
            with open(path, "rb") as handle:
                head = handle.read(HEADER_READ_BYTES)
        except OSError as exc:
            return ArchiveInfo(
                format="gzip",
                note=f"the file could not be read: {exc}")
        # A .tar.gz is a tar archive wearing gzip magic.
        try:
            with gzip.open(path, "rb") as handle:
                inner = handle.read(512)
        except (OSError, EOFError):
            inner = b""
        if inner[257:262] == b"ustar":
            return _list_tar(path)
        return _describe_gzip(path, head)
    return ArchiveInfo(
        format=fmt or "unknown",
        note=("no stdlib reader lists this format, so the "
              "member listing is unavailable on this road; "
              "the file is described from its header magic "
              "only, and nothing was extracted"))


# ---------------------------------------------------------------------------
# Roles — the account the map notes
# ---------------------------------------------------------------------------

_TEST_DIRS = {"tests", "test", "fixtures", "testdata", "test_data",
              "testing"}
_DOC_DIRS = {"docs", "doc", "documentation"}
_DATA_DIRS = {"data", "datasets", "dataset"}
_MEDIA_DIRS = {"assets", "static", "media", "images", "img",
               "public", "resources"}
_BACKUP_WORDS = ("backup", "snapshot", "dump", "export", "archive")


def asset_role(rel_path: str, kind: str, fmt: str = "") -> Tuple[str, str]:
    """(role, evidence) for one asset, from named rules.

    The rules are path-and-kind rules and say so; a file
    no rule claims takes its role from its kind, with
    that absence recorded as the evidence.
    """
    parts = [p.lower() for p in Path(rel_path).parts]
    dirs = parts[:-1]
    name = parts[-1] if parts else ""
    if any(part in _TEST_DIRS for part in dirs):
        return "test fixture", "its path runs through a test directory"
    if any(part in _DOC_DIRS for part in dirs):
        return "documentation asset", \
            "its path runs through a documentation directory"
    if any(part in _DATA_DIRS for part in dirs):
        return "data file", "its path runs through a data directory"
    if kind == "archive" and any(word in name for word in _BACKUP_WORDS):
        return "backup or snapshot archive", \
            "its name carries a backup word"
    if any(part in _MEDIA_DIRS for part in dirs):
        return "project asset", \
            "its path runs through a media/assets directory"
    if kind == "image":
        return "image asset", "no path rule matched; role from its kind"
    if kind == "archive":
        return "archive", "no path rule matched; role from its kind"
    return "large file", "no path rule matched; role from its kind"


# ---------------------------------------------------------------------------
# The scan
# ---------------------------------------------------------------------------

@dataclass
class AssetFile:
    """One asset's whole account."""

    path: str
    kind: str = ""  # image | archive | large
    format: str = ""
    size_bytes: int = 0
    large: bool = False
    image: Optional[ImageInfo] = None
    archive: Optional[ArchiveInfo] = None
    lines: int = 0
    role: str = ""
    role_evidence: str = ""
    note: str = ""

    def record(self) -> Dict[str, Any]:
        return {"path": self.path, "kind": self.kind,
                "format": self.format,
                "size_bytes": self.size_bytes,
                "large": self.large,
                "image": self.image.record() if self.image else None,
                "archive": self.archive.record()
                if self.archive else None,
                "lines": self.lines, "role": self.role,
                "role_evidence": self.role_evidence,
                "note": self.note}


def find_asset_files(
        workspace: Any) -> Tuple[List[Path], List[str]]:
    """Every asset candidate in the workspace, caps named.

    Candidates are files whose name claims an asset
    kind, files whose head bytes prove one, and files
    at or over the large threshold; the head read is
    bounded and a file that cannot be read is skipped
    with its reason.
    """
    root = Path(workspace)
    found: List[Path] = []
    warnings: List[str] = []
    if not root.is_dir():
        return found, warnings
    for candidate in sorted(root.rglob("*")):
        if not candidate.is_file():
            continue
        if any(part in _SKIP_DIRS or part.startswith(".venv")
               for part in candidate.parts):
            continue
        try:
            size = candidate.stat().st_size
            with open(candidate, "rb") as handle:
                head = handle.read(512)
        except OSError:
            continue
        if not classify_asset(candidate, size, head):
            continue
        if len(found) >= MAX_SCAN_FILES:
            warnings.append(
                f"scan capped at {MAX_SCAN_FILES} asset "
                "files; further files were not read")
            break
        found.append(candidate)
    return found, warnings


def _count_lines(path: Path) -> Tuple[int, bool]:
    """(lines, capped) for a text file, counted by streaming."""
    lines = 0
    read = 0
    capped = False
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1_000_000)
            if not chunk:
                break
            read += len(chunk)
            lines += chunk.count(b"\n")
            if read >= LINE_COUNT_CAP_BYTES:
                capped = True
                break
    return lines, capped


def describe_asset(root: Path, path: Path) -> AssetFile:
    """One asset's full description — headers/listings only."""
    try:
        display = str(path.relative_to(root))
    except ValueError:
        display = str(path)
    size = path.stat().st_size
    with open(path, "rb") as handle:
        head = handle.read(HEADER_READ_BYTES)
    kind = classify_asset(path, size, head)
    asset = AssetFile(
        path=display, kind=kind, size_bytes=size,
        large=size >= LARGE_FILE_BYTES)
    if kind == "image":
        info = describe_image(head)
        asset.format = info.format or _extension_of(path.name).lstrip(".")
        asset.image = info
        if not info.width and not info.height:
            asset.note = ("the header did not yield dimensions: "
                          + info.detail)
    elif kind == "archive":
        info = list_archive(path, _magic_archive_format(head))
        asset.format = info.format
        asset.archive = info
        if info.note and not info.members:
            asset.note = info.note
    elif kind == "large":
        asset.format = _extension_of(path.name).lstrip(".")
        if b"\x00" not in head[:8192]:
            lines, capped = _count_lines(path)
            asset.lines = lines
            asset.note = ("large text file; lines counted by "
                          "streaming, content never retained"
                          + ("; the count stopped at the "
                             f"{LINE_COUNT_CAP_BYTES}-byte cap, so "
                             "the line count is a floor"
                             if capped else ""))
        else:
            asset.note = ("large binary file of no recognised "
                          "image or archive kind; described by "
                          "size alone")
    asset.role, asset.role_evidence = asset_role(
        display, kind, asset.format)
    return asset


@dataclass
class AssetReport:
    """One asset-sight call's whole account."""

    kind: str = "show"  # show | file | images | archives | large
    status: str = "ok"  # ok | disabled | error
    files: List[AssetFile] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    note: str = ""

    def totals(self) -> Tuple[int, int, int, int]:
        """(files, images, archives, large files)."""
        return (len(self.files),
                sum(1 for f in self.files if f.kind == "image"),
                sum(1 for f in self.files if f.kind == "archive"),
                sum(1 for f in self.files if f.large))

    def file_names(self) -> Tuple[str, ...]:
        return tuple(f.path for f in self.files)

    def image_names(self) -> Tuple[str, ...]:
        return tuple(f.path for f in self.files if f.kind == "image")

    def archive_names(self) -> Tuple[str, ...]:
        return tuple(f.path for f in self.files if f.kind == "archive")

    def large_names(self) -> Tuple[str, ...]:
        return tuple(f.path for f in self.files if f.large)

    def record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "status": self.status,
                "files": [f.record() for f in self.files],
                "warnings": list(self.warnings),
                "note": self.note}


def _closed(kind: str) -> AssetReport:
    return AssetReport(
        kind=kind, status="disabled",
        note=("asset sight is off (the asset_sight "
              "setting), so no project file was read"))


def asset_sight(
        workspace: Any, mode: str = "show", *,
        target: Optional[str] = None,
        enabled: bool = True,
) -> AssetReport:
    """One asset account — all assets, one file, or one kind.

    Read-only header and listing reads; nothing is
    decoded, extracted or executed. A missing workspace
    is an honest ``error`` report. Raises
    :class:`ValueError` for an unknown mode.
    """
    kind = (mode or "show").strip().lower()
    if kind not in ("show", "file", "images", "archives", "large"):
        raise ValueError(f"{USAGE} — unknown mode {mode!r}")
    if not enabled:
        return _closed(kind)
    root = Path(workspace)
    if not root.is_dir():
        return AssetReport(
            kind=kind, status="error",
            note=f"no workspace at {root} — nothing was read")
    if kind == "file":
        if not target:
            raise ValueError(f"{USAGE} — this road needs its file")
        candidate = Path(target)
        if not candidate.is_absolute():
            candidate = root / candidate
        if not candidate.is_file():
            return AssetReport(
                kind=kind, status="error",
                note=f"no file at {target} — nothing was read")
        try:
            size = candidate.stat().st_size
            with open(candidate, "rb") as handle:
                head = handle.read(512)
        except OSError as exc:
            return AssetReport(
                kind=kind, status="error",
                note=f"the file could not be read: {exc}")
        if not classify_asset(candidate, size, head):
            return AssetReport(
                kind=kind, status="error",
                note=(f"{target} is not an asset asset sight "
                      "knows — images, archives, and files at "
                      f"or over {LARGE_FILE_BYTES} bytes are "
                      "described"))
        report = AssetReport(kind=kind)
        report.files = [describe_asset(root, candidate)]
        report.note = ("one file described from its header or "
                       "listing — nothing was dumped")
        return report
    found, warnings = find_asset_files(root)
    report = AssetReport(kind=kind)
    report.warnings.extend(warnings)
    for path in found:
        try:
            asset = describe_asset(root, path)
        except OSError as exc:
            report.warnings.append(
                f"{path} skipped: could not be read ({exc})")
            continue
        if kind == "images" and asset.kind != "image":
            continue
        if kind == "archives" and asset.kind != "archive":
            continue
        if kind == "large" and not asset.large:
            continue
        report.files.append(asset)
    report.note = (
        "files described from headers and listings — "
        "nothing was dumped, decoded or extracted"
        if report.files else
        "no asset files in this workspace — images, "
        "archives, and files at or over "
        f"{LARGE_FILE_BYTES} bytes are recognised wherever "
        "they land")
    return report


# ---------------------------------------------------------------------------
# Surfaces: the shared parser + formatters
# ---------------------------------------------------------------------------

def parse_assets_args(arguments: str) -> Dict[str, Any]:
    """Parse ``/assets`` arguments into an asset request.

    Grammar::

        /assets
        /assets show
        /assets <file>
        /assets images | archives | large

    Raises :class:`ValueError` on a usage error.
    """
    text = (arguments or "").strip()
    if not text:
        return {"action": "show"}
    tokens = text.split()
    if len(tokens) != 1:
        raise ValueError(f"{USAGE} — name one file, or none")
    head = tokens[0].lower()
    if head in ("show", "images", "archives", "large"):
        return {"action": head}
    return {"action": "file", "target": tokens[0]}


def format_asset_report(status: Dict[str, Any]) -> str:
    """One asset call's account, from an Agent status mapping."""
    report = status["report"]
    lines = [f"Asset sight ({ASSET_SLICE}): {report['kind']} — "
             "binary and asset files described, never dumped."]
    for entry in report["files"]:
        bits = [f"{entry['size_bytes']} byte(s)"]
        image = entry.get("image")
        if image:
            bits.append(
                f"{image['format']} "
                f"{image['width']}x{image['height']}"
                if image["width"] else
                f"{image['format']} (dimensions not read)")
            if image["detail"]:
                bits.append(image["detail"])
        archive = entry.get("archive")
        if archive:
            bits.append(
                f"{archive['format']} archive, "
                f"{archive['member_count']} member(s), "
                f"{archive['total_size']} byte(s) uncompressed")
        if entry["lines"]:
            bits.append(f"{entry['lines']} line(s)")
        lines.append(
            f"  {entry['path']} [{entry['kind']}]: "
            + "; ".join(bits))
        lines.append(
            f"    role: {entry['role']} ({entry['role_evidence']})")
        if archive and archive["members"]:
            for member in archive["members"]:
                lines.append(
                    f"    - {member['name']} "
                    f"({member['size']} byte(s))")
        if entry["note"]:
            lines.append(f"    {entry['note']}")
    if report["note"]:
        lines.append(f"  {report['note']}")
    for warning in report["warnings"]:
        lines.append(f"  Warning: {warning}")
    lines.append(status["plain_explanation"])
    return "\n".join(lines)


def render_markdown(report: AssetReport) -> str:
    """Render *report* as a human report, from its own record.

    Built from :meth:`AssetReport.totals`,
    :meth:`AssetReport.file_names` /
    :meth:`AssetReport.image_names` /
    :meth:`AssetReport.archive_names` /
    :meth:`AssetReport.large_names` and each asset's own
    accessors, so the rendered page is computed from the
    same values the tests pin.
    """
    n_files, n_images, n_archives, n_large = report.totals()
    lines = [
        "# Asset Sight — binary and asset files, described",
        "",
        f"*Slice {ASSET_SLICE} of the All-Features road "
        "(Part III — Code Intelligence). Read-only — "
        "nothing is decoded, extracted or dumped by this "
        "report.*",
        "",
        f"**{n_files} asset(s)**, **{n_images} image(s)**, "
        f"**{n_archives} archive(s)**, **{n_large} large**.",
        "",
    ]
    for entry in report.files:
        bits = [f"{entry.size_bytes} byte(s)"]
        if entry.image is not None:
            bits.append(
                f"{entry.image.format} "
                f"{entry.image.dimensions()}")
        if entry.archive is not None:
            names = ", ".join(entry.archive.member_names())
            bits.append(
                f"{entry.archive.format} archive, "
                f"{entry.archive.member_count} member(s)"
                + (f": {names}" if names else ""))
        if entry.lines:
            bits.append(f"{entry.lines} line(s)")
        lines.append(
            f"- `{entry.path}` [{entry.kind}]: "
            + "; ".join(bits)
            + f" — role: {entry.role} ({entry.role_evidence})")
    lines.append("")
    lines.append(
        "Files described: "
        + (", ".join(report.file_names()) or "none"))
    lines.append(
        "Images: " + (", ".join(report.image_names()) or "none"))
    lines.append(
        "Archives: " + (", ".join(report.archive_names()) or "none"))
    lines.append(
        "Large files: " + (", ".join(report.large_names()) or "none"))
    lines.append("")
    return "\n".join(lines)

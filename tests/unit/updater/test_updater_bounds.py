import json
from pathlib import Path
from unittest.mock import patch

import pytest

from updater import Updater


def test_extract_file_retries_bounded_times():
    updater = object.__new__(Updater)
    updater.exe_path = "missing-7za.exe"
    updater.download_file_path = "missing-update.7z"
    updater.temp_path = "./update_temp"

    with patch("updater.safe_unpack_archive", side_effect=RuntimeError("broken")) as mock_unpack:
        with pytest.raises(RuntimeError, match="解压更新包失败"):
            updater.extract_file()

    assert mock_unpack.call_count == 3


def test_prepare_update_payload_raises_when_extract_fails():
    updater = object.__new__(Updater)
    updater.extract_folder_path = "./update_temp"

    with patch.object(updater, "extract_file", side_effect=RuntimeError("broken")):
        with pytest.raises(RuntimeError, match="准备更新包失败"):
            updater._prepare_update_payload(False)


@pytest.mark.parametrize(
    "path",
    [
        "../outside.txt", r"..\outside.txt", "nested/../../outside.txt", "/outside.txt", r"\outside.txt",
        "C:/outside.txt", "C:outside.txt", r"\\server\share\outside.txt", "nested/file.txt:stream",
        "nested/.. /outside.txt", "", ".",
    ],
)
def test_normalize_manifest_path_rejects_parent_traversal_and_absolute_paths(path):
    updater = object.__new__(Updater)
    updater.extract_folder_path = "update_temp/AALC"

    with pytest.raises(ValueError):
        updater._normalize_manifest_path(path)


def _incremental_updater(tmp_path, changes):
    updater = object.__new__(Updater)
    updater.cover_folder_path = str(tmp_path / "install")
    updater.extract_folder_path = str(tmp_path / "payload" / "AALC")
    updater.changes_file_path = str(tmp_path / "changes.json")
    Path(updater.cover_folder_path).mkdir()
    Path(updater.extract_folder_path).mkdir(parents=True)
    Path(updater.changes_file_path).write_text(json.dumps(changes), encoding="utf-8")
    return updater


@pytest.mark.parametrize("category", ["deleted", "deleted_dir"])
def test_incremental_update_never_removes_outside_install_root(tmp_path, category):
    if category == "deleted_dir":
        outside = tmp_path / "outside"
        outside.mkdir()
        sentinel = outside / "sentinel.txt"
        unsafe_path = "../outside"
    else:
        sentinel = tmp_path / "outside.txt"
        unsafe_path = "../outside.txt"
    sentinel.write_bytes(b"keep outside install")
    updater = _incremental_updater(tmp_path, {category: [unsafe_path]})

    with pytest.raises(ValueError):
        updater._apply_incremental_update()

    assert sentinel.read_bytes() == b"keep outside install"


def test_incremental_update_never_creates_directory_outside_install_root(tmp_path):
    updater = _incremental_updater(tmp_path, {"added_dir": ["../outside_created"]})

    with pytest.raises(ValueError):
        updater._apply_incremental_update()

    assert not (tmp_path / "outside_created").exists()


@pytest.mark.parametrize("category", ["added", "modified"])
def test_incremental_update_never_copies_outside_install_root(tmp_path, category):
    sentinel = tmp_path / "outside.txt"
    sentinel.write_bytes(b"keep outside install")
    updater = _incremental_updater(tmp_path, {category: ["../outside.txt"]})
    (Path(updater.extract_folder_path).parent / "outside.txt").write_bytes(b"untrusted replacement")

    with pytest.raises(ValueError):
        updater._apply_incremental_update()

    assert sentinel.read_bytes() == b"keep outside install"


def test_incremental_update_validates_all_paths_before_mutation(tmp_path):
    updater = _incremental_updater(tmp_path, {"deleted": ["safe.txt", "../outside.txt"]})
    safe_file = Path(updater.cover_folder_path) / "safe.txt"
    safe_file.write_bytes(b"keep valid file on rejected manifest")
    sentinel = tmp_path / "outside.txt"
    sentinel.write_bytes(b"keep outside install")

    with pytest.raises(ValueError):
        updater._apply_incremental_update()

    assert safe_file.read_bytes() == b"keep valid file on rejected manifest"
    assert sentinel.read_bytes() == b"keep outside install"


def test_incremental_update_preserves_valid_nested_and_archive_root_paths(tmp_path):
    updater = _incremental_updater(
        tmp_path,
        {
            "deleted": ["AALC/nested/old.txt"],
            "added_dir": ["AALC/empty"],
            "added": ["nested/new.txt"],
            "modified": [r"AALC\nested\existing.txt"],
        },
    )
    install = Path(updater.cover_folder_path)
    extracted = Path(updater.extract_folder_path)
    (install / "nested").mkdir()
    (install / "nested" / "old.txt").write_bytes(b"remove me")
    (install / "nested" / "existing.txt").write_bytes(b"old")
    (extracted / "nested").mkdir()
    (extracted / "nested" / "new.txt").write_bytes(b"new")
    (extracted / "nested" / "existing.txt").write_bytes(b"updated")

    updater._apply_incremental_update()

    assert not (install / "nested" / "old.txt").exists()
    assert (install / "empty").is_dir()
    assert (install / "nested" / "new.txt").read_bytes() == b"new"
    assert (install / "nested" / "existing.txt").read_bytes() == b"updated"


def test_incremental_update_rejects_install_link_outside_root(tmp_path):
    updater = _incremental_updater(tmp_path, {"deleted": ["linked/sentinel.txt"]})
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel.txt"
    sentinel.write_bytes(b"keep linked file")
    try:
        (Path(updater.cover_folder_path) / "linked").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Creating symbolic links is unavailable")

    with pytest.raises(ValueError):
        updater._apply_incremental_update()

    assert sentinel.read_bytes() == b"keep linked file"

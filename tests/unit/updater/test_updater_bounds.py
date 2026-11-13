import json
import os
import shutil
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


@pytest.mark.parametrize("category", ["added", "modified"])
def test_incremental_update_fails_when_required_source_file_is_missing(
    tmp_path, category
):
    updater = _incremental_updater(tmp_path, {category: ["nested/required.txt"]})
    if category == "modified":
        installed_file = Path(updater.cover_folder_path) / "nested" / "required.txt"
        installed_file.parent.mkdir()
        installed_file.write_bytes(b"previous version")

    with pytest.raises(RuntimeError, match="required.txt"):
        updater._apply_incremental_update()


def test_run_reports_apply_failure_and_keeps_update_payload(capsys):
    updater = object.__new__(Updater)
    with (
        patch.object(updater, "_prepare_update_payload") as prepare,
        patch.object(updater, "terminate_processes") as terminate,
        patch.object(updater, "cover_folder", side_effect=OSError("copy failed")) as cover,
        patch.object(updater, "cleanup") as cleanup,
        patch("builtins.input") as wait_for_exit,
        patch("updater.subprocess.run") as launch,
        patch("updater.subprocess.Popen") as launch_fallback,
    ):
        result = updater.run(apply_mode=True)

    assert result is False
    prepare.assert_called_once_with(True)
    terminate.assert_called_once_with()
    cover.assert_called_once_with()
    cleanup.assert_not_called()
    wait_for_exit.assert_not_called()
    launch.assert_not_called()
    launch_fallback.assert_not_called()
    assert "应用更新失败" in capsys.readouterr().out


def test_missing_update_source_fails_before_deleting_valid_files(tmp_path):
    updater = _incremental_updater(
        tmp_path,
        {
            "deleted": ["nested/old.txt"],
            "added": ["nested/required.txt"],
        },
    )
    old_file = Path(updater.cover_folder_path) / "nested" / "old.txt"
    old_file.parent.mkdir()
    old_file.write_bytes(b"keep until update payload is complete")

    with pytest.raises(RuntimeError, match="required.txt"):
        updater._apply_incremental_update()

    assert old_file.read_bytes() == b"keep until update payload is complete"


def test_run_can_retry_after_partial_incremental_copy(tmp_path):
    changes = {
        "deleted": ["nested/old.txt"],
        "added": ["nested/new.txt"],
        "modified": ["nested/existing.txt"],
    }
    updater = _incremental_updater(tmp_path, changes)
    updater.download_file_path = None
    install = Path(updater.cover_folder_path) / "nested"
    extracted = Path(updater.extract_folder_path) / "nested"
    install.mkdir()
    extracted.mkdir()
    old_file = install / "old.txt"
    old_file.write_bytes(b"obsolete")
    new_file = extracted / "new.txt"
    new_file.write_bytes(b"new")
    existing_file = install / "existing.txt"
    existing_file.write_bytes(b"old version")
    (extracted / "existing.txt").write_bytes(b"updated version")
    real_copy2 = shutil.copy2
    copy_calls = 0

    def fail_on_second_copy(source, destination):
        nonlocal copy_calls
        copy_calls += 1
        if copy_calls == 2:
            raise OSError("disk full")
        return real_copy2(source, destination)

    with (
        patch.object(updater, "terminate_processes") as terminate,
        patch("builtins.input"),
        patch("updater.subprocess.run"),
        patch("updater.subprocess.Popen"),
    ):
        with patch("updater.shutil.copy2", side_effect=fail_on_second_copy):
            assert updater.run(apply_mode=True) is False

        assert not old_file.exists()
        assert (install / "new.txt").read_bytes() == b"new"
        assert existing_file.read_bytes() == b"old version"
        assert Path(updater.extract_folder_path).is_dir()
        assert Path(updater.changes_file_path).is_file()

        assert updater.run(apply_mode=True) is None

    assert terminate.call_count == 2
    assert not old_file.exists()
    assert (install / "new.txt").read_bytes() == b"new"
    assert existing_file.read_bytes() == b"updated version"
    assert not Path(updater.extract_folder_path).exists()
    assert not Path(updater.changes_file_path).exists()


def test_run_can_retry_after_partial_incremental_delete(tmp_path):
    updater = _incremental_updater(
        tmp_path,
        {"deleted": ["nested/first.txt", "nested/second.txt"]},
    )
    updater.download_file_path = None
    install = Path(updater.cover_folder_path) / "nested"
    install.mkdir()
    first_file = install / "first.txt"
    second_file = install / "second.txt"
    first_file.write_bytes(b"first obsolete file")
    second_file.write_bytes(b"second obsolete file")
    sentinel = tmp_path / "outside.txt"
    sentinel.write_bytes(b"keep outside install")
    changes_file = Path(updater.changes_file_path)
    extract_folder = Path(updater.extract_folder_path)
    real_remove = os.remove

    def fail_second_delete(path, *args, **kwargs):
        if Path(path) == second_file:
            raise PermissionError("file is in use")
        return real_remove(path, *args, **kwargs)

    with (
        patch.object(updater, "terminate_processes"),
        patch("builtins.input"),
        patch("updater.subprocess.run"),
        patch("updater.subprocess.Popen"),
    ):
        with patch("updater.os.remove", side_effect=fail_second_delete):
            assert updater.run(apply_mode=True) is False

        assert not first_file.exists()
        assert second_file.read_bytes() == b"second obsolete file"
        assert sentinel.read_bytes() == b"keep outside install"
        assert changes_file.is_file()
        assert extract_folder.is_dir()

        assert updater.run(apply_mode=True) is None

    assert not first_file.exists()
    assert not second_file.exists()
    assert sentinel.read_bytes() == b"keep outside install"
    assert not changes_file.exists()
    assert not extract_folder.exists()


def test_incremental_update_retries_after_partial_directory_delete(tmp_path):
    updater = _incremental_updater(tmp_path, {"deleted_dir": ["obsolete"]})
    obsolete_dir = Path(updater.cover_folder_path) / "obsolete"
    obsolete_dir.mkdir()
    first_file = obsolete_dir / "first.txt"
    second_file = obsolete_dir / "second.txt"
    first_file.write_bytes(b"first obsolete file")
    second_file.write_bytes(b"second obsolete file")
    sentinel = tmp_path / "outside.txt"
    sentinel.write_bytes(b"keep outside install")
    real_rmtree = shutil.rmtree

    def fail_after_partial_delete(path, *args, **kwargs):
        if Path(path) == obsolete_dir:
            first_file.unlink()
            raise PermissionError("directory is in use")
        return real_rmtree(path, *args, **kwargs)

    with patch("updater.shutil.rmtree", side_effect=fail_after_partial_delete):
        with pytest.raises(PermissionError, match="directory is in use"):
            updater._apply_incremental_update()

    assert not first_file.exists()
    assert second_file.read_bytes() == b"second obsolete file"
    assert sentinel.read_bytes() == b"keep outside install"

    updater._apply_incremental_update()

    assert not obsolete_dir.exists()
    assert sentinel.read_bytes() == b"keep outside install"


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

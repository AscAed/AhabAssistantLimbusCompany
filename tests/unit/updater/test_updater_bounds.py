import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

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


def test_terminate_processes_ignores_unavailable_process_name():
    updater = object.__new__(Updater)
    updater.process_names = ["AALC.exe"]
    unnamed_process = Mock(info={"pid": 101, "name": None})
    unrelated_process = Mock(info={"pid": 102, "name": "other.exe"})
    target_process = Mock(info={"pid": 103, "name": "AALC.exe"})

    with patch(
        "updater.psutil.process_iter",
        return_value=[unnamed_process, unrelated_process, target_process],
    ):
        updater.terminate_processes()

    unnamed_process.terminate.assert_not_called()
    unrelated_process.terminate.assert_not_called()
    target_process.terminate.assert_called_once_with()
    target_process.wait.assert_called_once_with(timeout=10)


def test_extract_file_recovers_after_process_exit_during_safe_unpack(tmp_path):
    archive_path = tmp_path / "update_temp" / "AALC.zip"
    archive_path.parent.mkdir()
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("AALC/nested/first.bin", b"complete first file")
        archive.writestr("AALC/nested/second.bin", b"complete second file")

    child_environment = os.environ.copy()
    project_root = Path(__file__).resolve().parents[3]
    child_environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, (str(project_root), child_environment.get("PYTHONPATH")))
    )
    interrupted_unpack_script = """
import os
import sys
from pathlib import Path
from unittest.mock import patch

from updater import Updater

updater = Updater(sys.argv[1])

def exit_after_partial_unpack(archive_path, extract_dir, format=None):
    partial_file = Path(extract_dir) / "AALC" / "nested" / "first.bin"
    partial_file.parent.mkdir(parents=True, exist_ok=True)
    with open(partial_file, "wb") as output:
        output.write(b"partial")
        output.flush()
        os.fsync(output.fileno())
    os._exit(86)

with patch("updater.safe_unpack_archive", side_effect=exit_after_partial_unpack):
    updater.extract_file()
"""
    interrupted_result = subprocess.run(
        [sys.executable, "-c", interrupted_unpack_script, archive_path.name],
        cwd=tmp_path,
        env=child_environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    extract_folder = tmp_path / "update_temp" / "AALC"
    first_file = extract_folder / "nested" / "first.bin"
    second_file = extract_folder / "nested" / "second.bin"
    assert interrupted_result.returncode == 86, (
        interrupted_result.stdout + interrupted_result.stderr
    )
    assert first_file.read_bytes() == b"partial"
    assert not second_file.exists()

    restart_script = """
import sys

from updater import Updater

updater = Updater(sys.argv[1])
updater.extract_file()
"""
    restart_result = subprocess.run(
        [sys.executable, "-c", restart_script, archive_path.name],
        cwd=tmp_path,
        env=child_environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert restart_result.returncode == 0, restart_result.stdout + restart_result.stderr
    assert first_file.read_bytes() == b"complete first file"
    assert second_file.read_bytes() == b"complete second file"
    assert archive_path.is_file()


def test_extract_file_uses_bundled_7za_for_zip_archive(tmp_path):
    archive_path = tmp_path / "update_temp" / "AALC.zip"
    archive_path.parent.mkdir()
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("AALC/nested/first.bin", b"first file")
        archive.writestr("AALC/nested/second.bin", b"second file")

    updater = object.__new__(Updater)
    updater.exe_path = str(
        Path(__file__).resolve().parents[3] / "assets" / "binary" / "7za.exe"
    )
    updater.download_file_path = str(archive_path)
    updater.temp_path = str(archive_path.parent)
    extract_folder = archive_path.parent / "AALC"

    assert Path(updater.exe_path).is_file()
    assert updater.extract_file() is True
    assert (extract_folder / "nested" / "first.bin").read_bytes() == b"first file"
    assert (extract_folder / "nested" / "second.bin").read_bytes() == b"second file"


def test_extract_file_replays_partial_output_through_bundled_7za(tmp_path):
    archive_path = tmp_path / "update_temp" / "AALC.zip"
    archive_path.parent.mkdir()
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("AALC/nested/first.bin", b"complete first file")
        archive.writestr("AALC/nested/second.bin", b"complete second file")

    exe_path = Path(__file__).resolve().parents[3] / "assets" / "binary" / "7za.exe"
    child_environment = os.environ.copy()
    project_root = Path(__file__).resolve().parents[3]
    child_environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, (str(project_root), child_environment.get("PYTHONPATH")))
    )
    interrupted_unpack_script = """
import os
import sys
from pathlib import Path
from unittest.mock import patch

from updater import Updater

updater = Updater(sys.argv[1])
updater.exe_path = sys.argv[2]

def exit_with_partial_extraction(command, check):
    assert command[0] == updater.exe_path
    assert command[1:3] == ["x", updater.download_file_path]
    assert check is True
    partial_file = Path(updater.temp_path) / "AALC" / "nested" / "first.bin"
    partial_file.parent.mkdir(parents=True, exist_ok=True)
    with open(partial_file, "wb") as output:
        output.write(b"partial")
        output.flush()
        os.fsync(output.fileno())
    os._exit(88)

with patch("updater.subprocess.run", side_effect=exit_with_partial_extraction):
    updater.extract_file()
"""
    interrupted_result = subprocess.run(
        [
            sys.executable,
            "-c",
            interrupted_unpack_script,
            archive_path.name,
            str(exe_path),
        ],
        cwd=tmp_path,
        env=child_environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    extract_folder = archive_path.parent / "AALC"
    first_file = extract_folder / "nested" / "first.bin"
    second_file = extract_folder / "nested" / "second.bin"
    assert interrupted_result.returncode == 88, (
        interrupted_result.stdout + interrupted_result.stderr
    )
    assert first_file.read_bytes() == b"partial"
    assert not second_file.exists()

    restart_script = """
import sys

from updater import Updater

updater = Updater(sys.argv[1])
updater.exe_path = sys.argv[2]
updater.extract_file()
"""
    restart_result = subprocess.run(
        [
            sys.executable,
            "-c",
            restart_script,
            archive_path.name,
            str(exe_path),
        ],
        cwd=tmp_path,
        env=child_environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert restart_result.returncode == 0, restart_result.stdout + restart_result.stderr
    assert first_file.read_bytes() == b"complete first file"
    assert second_file.read_bytes() == b"complete second file"
    assert archive_path.is_file()


def test_updater_staging_recovers_after_process_exit_during_copy(tmp_path):
    source_folder = tmp_path / "source"
    source_folder.mkdir()
    source_updater = source_folder / "Update.exe"
    source_updater.write_bytes(b"complete updater payload")
    install_folder = tmp_path / "install"
    install_folder.mkdir()
    staged_updater = install_folder / "update_temp" / "Update.exe"
    launch_record = tmp_path / "launch.json"

    child_environment = os.environ.copy()
    project_root = Path(__file__).resolve().parents[3]
    child_environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, (str(project_root), child_environment.get("PYTHONPATH")))
    )
    interrupted_copy_script = """
import os
import sys
from unittest.mock import patch

from updater import check_temp_dir_and_run

source_path = sys.argv[1]
sys.frozen = True
sys.argv = [source_path, "payload.7z"]

def exit_after_partial_copy(source, destination):
    with open(destination, "wb") as staged:
        staged.write(b"partial")
        staged.flush()
        os.fsync(staged.fileno())
    os._exit(84)

with patch("updater.shutil.copy", side_effect=exit_after_partial_copy):
    check_temp_dir_and_run()
"""
    interrupted_result = subprocess.run(
        [sys.executable, "-c", interrupted_copy_script, str(source_updater)],
        cwd=install_folder,
        env=child_environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert interrupted_result.returncode == 84, (
        interrupted_result.stdout + interrupted_result.stderr
    )
    assert staged_updater.read_bytes() == b"partial"
    assert not launch_record.exists()

    restart_script = """
import json
import sys
from pathlib import Path
from unittest.mock import patch

from updater import check_temp_dir_and_run

source_path, record_path = sys.argv[1:3]
sys.frozen = True
sys.argv = [source_path, "payload.7z"]

def record_launch(args, **kwargs):
    Path(record_path).write_text(json.dumps(args), encoding="utf-8")

with patch("updater.subprocess.Popen", side_effect=record_launch):
    check_temp_dir_and_run()
"""
    restart_result = subprocess.run(
        [
            sys.executable,
            "-c",
            restart_script,
            str(source_updater),
            str(launch_record),
        ],
        cwd=install_folder,
        env=child_environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert restart_result.returncode == 0, restart_result.stdout + restart_result.stderr
    assert staged_updater.read_bytes() == source_updater.read_bytes()
    assert json.loads(launch_record.read_text(encoding="utf-8")) == [
        str(staged_updater),
        "payload.7z",
    ]


def test_handoff_recovers_after_process_exit_during_updater_copy(tmp_path):
    install_folder = tmp_path / "install"
    extract_folder = install_folder / "update_temp" / "AALC"
    extract_folder.mkdir(parents=True)
    source_updater = extract_folder / "AALC Updater.exe"
    source_updater.write_bytes(b"complete updater payload")
    staged_updater = install_folder / "update_temp" / "AALC Updater.apply.exe"
    launch_record = tmp_path / "launch.json"

    child_environment = os.environ.copy()
    project_root = Path(__file__).resolve().parents[3]
    child_environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, (str(project_root), child_environment.get("PYTHONPATH")))
    )
    interrupted_copy_script = """
import os
import sys
from unittest.mock import patch

from updater import Updater

install_folder, extract_folder = sys.argv[1:3]
updater = object.__new__(Updater)
updater.file_name = "AALC.7z"
updater.updater_name = "AALC Updater.exe"
updater.extract_folder_path = extract_folder
updater.temp_path = os.path.join(install_folder, "update_temp")
updater.apply_updater_name = "AALC Updater.apply.exe"
updater.cover_folder_path = install_folder

def exit_after_partial_copy(source, destination):
    with open(destination, "wb") as staged:
        staged.write(b"partial")
        staged.flush()
        os.fsync(staged.fileno())
    os._exit(83)

with patch("updater.shutil.copy2", side_effect=exit_after_partial_copy):
    updater._handoff_to_new_updater()
"""
    interrupted_result = subprocess.run(
        [
            sys.executable,
            "-c",
            interrupted_copy_script,
            str(install_folder),
            str(extract_folder),
        ],
        cwd=install_folder,
        env=child_environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert interrupted_result.returncode == 83, (
        interrupted_result.stdout + interrupted_result.stderr
    )
    assert staged_updater.read_bytes() == b"partial"
    assert not launch_record.exists()

    restart_script = """
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

from updater import Updater

install_folder, extract_folder, record_path = sys.argv[1:4]
updater = object.__new__(Updater)
updater.file_name = "AALC.7z"
updater.updater_name = "AALC Updater.exe"
updater.extract_folder_path = extract_folder
updater.temp_path = os.path.join(install_folder, "update_temp")
updater.apply_updater_name = "AALC Updater.apply.exe"
updater.cover_folder_path = install_folder

def record_launch(args, **kwargs):
    Path(record_path).write_text(json.dumps([args, kwargs["cwd"]]), encoding="utf-8")

with patch("updater.subprocess.Popen", side_effect=record_launch):
    assert updater._handoff_to_new_updater() is True
"""
    restart_result = subprocess.run(
        [
            sys.executable,
            "-c",
            restart_script,
            str(install_folder),
            str(extract_folder),
            str(launch_record),
        ],
        cwd=install_folder,
        env=child_environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert restart_result.returncode == 0, restart_result.stdout + restart_result.stderr
    assert staged_updater.read_bytes() == source_updater.read_bytes()
    launch_args, launch_cwd = json.loads(launch_record.read_text(encoding="utf-8"))
    assert launch_args == [
        str(staged_updater),
        "--apply-update",
        "AALC.7z",
    ]
    assert launch_cwd == str(install_folder)


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


def _restart_incremental_updater(updater):
    restarted_updater = object.__new__(Updater)
    restarted_updater.cover_folder_path = updater.cover_folder_path
    restarted_updater.extract_folder_path = updater.extract_folder_path
    restarted_updater.changes_file_path = updater.changes_file_path
    restarted_updater.download_file_path = None
    return restarted_updater


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


def test_run_reports_apply_failure_and_keeps_update_payload(tmp_path, capsys):
    updater = object.__new__(Updater)
    updater.extract_folder_path = str(tmp_path / "payload")
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
        patch.object(Updater, "terminate_processes") as terminate,
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

        restarted_updater = _restart_incremental_updater(updater)
        assert restarted_updater.run(apply_mode=True) is None

    assert terminate.call_count == 2
    assert not old_file.exists()
    assert (install / "new.txt").read_bytes() == b"new"
    assert existing_file.read_bytes() == b"updated version"
    assert not Path(updater.extract_folder_path).exists()
    assert not Path(updater.changes_file_path).exists()


def test_incremental_update_recovers_after_process_exit_during_file_delete(tmp_path):
    updater = _incremental_updater(
        tmp_path,
        {
            "deleted": ["obsolete-first.txt", "obsolete-second.txt"],
            "added": ["new.txt"],
        },
    )
    first_file = Path(updater.cover_folder_path) / "obsolete-first.txt"
    second_file = Path(updater.cover_folder_path) / "obsolete-second.txt"
    first_file.write_bytes(b"remove first")
    second_file.write_bytes(b"remove second")
    outside_sentinel = tmp_path / "outside.txt"
    outside_sentinel.write_bytes(b"keep outside install")
    source_file = Path(updater.extract_folder_path) / "new.txt"
    source_file.write_bytes(b"new file")

    child_script = """
import os
import sys
from pathlib import Path
from unittest.mock import patch

from updater import Updater

updater = object.__new__(Updater)
updater.cover_folder_path, updater.extract_folder_path, updater.changes_file_path = sys.argv[1:4]
updater.download_file_path = None
exit_path = Path(sys.argv[4])
real_remove = os.remove

def exit_after_first_delete(path):
    if Path(path) == exit_path:
        real_remove(path)
        os._exit(77)
    return real_remove(path)

with patch.object(Updater, "terminate_processes"), patch(
    "updater.os.remove", side_effect=exit_after_first_delete
):
    updater.run(apply_mode=True)
"""
    project_root = Path(__file__).resolve().parents[3]
    child_environment = os.environ.copy()
    child_environment["PYTHONPATH"] = os.pathsep.join(
        filter(
            None,
            (str(project_root), child_environment.get("PYTHONPATH")),
        )
    )
    child_result = subprocess.run(
        [
            sys.executable,
            "-c",
            child_script,
            updater.cover_folder_path,
            updater.extract_folder_path,
            updater.changes_file_path,
            str(first_file),
        ],
        cwd=tmp_path,
        env=child_environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert child_result.returncode == 77, child_result.stdout + child_result.stderr
    assert not first_file.exists()
    assert second_file.read_bytes() == b"remove second"
    assert Path(updater.changes_file_path).is_file()
    assert source_file.read_bytes() == b"new file"
    assert not Path(updater._get_apply_complete_path()).exists()

    restarted_updater = _restart_incremental_updater(updater)
    with (
        patch.object(Updater, "terminate_processes"),
        patch("builtins.input"),
        patch("updater.subprocess.run"),
        patch("updater.subprocess.Popen"),
    ):
        assert restarted_updater.run(apply_mode=True) is None

    assert not first_file.exists()
    assert not second_file.exists()
    assert (Path(updater.cover_folder_path) / "new.txt").read_bytes() == b"new file"
    assert outside_sentinel.read_bytes() == b"keep outside install"
    assert not Path(updater.extract_folder_path).exists()
    assert not Path(updater.changes_file_path).exists()
    assert not Path(updater._get_apply_complete_path()).exists()


def test_incremental_update_recovers_after_process_exit_during_directory_delete(
    tmp_path,
):
    updater = _incremental_updater(
        tmp_path,
        {
            "deleted_dir": ["obsolete"],
            "added": ["new.txt"],
        },
    )
    obsolete_dir = Path(updater.cover_folder_path) / "obsolete"
    obsolete_dir.mkdir()
    first_file = obsolete_dir / "first.txt"
    second_file = obsolete_dir / "second.txt"
    first_file.write_bytes(b"remove first")
    second_file.write_bytes(b"remove second")
    outside_sentinel = tmp_path / "outside.txt"
    outside_sentinel.write_bytes(b"keep outside install")
    source_file = Path(updater.extract_folder_path) / "new.txt"
    source_file.write_bytes(b"new file")

    child_script = """
import os
import shutil
import sys
from pathlib import Path
from unittest.mock import patch

from updater import Updater

updater = object.__new__(Updater)
updater.cover_folder_path, updater.extract_folder_path, updater.changes_file_path = sys.argv[1:4]
updater.download_file_path = None
exit_path = Path(sys.argv[4])
real_rmtree = shutil.rmtree

def exit_after_partial_directory_delete(path, *args, **kwargs):
    if Path(path) == exit_path:
        (Path(path) / "first.txt").unlink()
        os._exit(78)
    return real_rmtree(path, *args, **kwargs)

with patch.object(Updater, "terminate_processes"), patch(
    "updater.shutil.rmtree", side_effect=exit_after_partial_directory_delete
):
    updater.run(apply_mode=True)
"""
    project_root = Path(__file__).resolve().parents[3]
    child_environment = os.environ.copy()
    child_environment["PYTHONPATH"] = os.pathsep.join(
        filter(
            None,
            (str(project_root), child_environment.get("PYTHONPATH")),
        )
    )
    child_result = subprocess.run(
        [
            sys.executable,
            "-c",
            child_script,
            updater.cover_folder_path,
            updater.extract_folder_path,
            updater.changes_file_path,
            str(obsolete_dir),
        ],
        cwd=tmp_path,
        env=child_environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert child_result.returncode == 78, child_result.stdout + child_result.stderr
    assert not first_file.exists()
    assert second_file.read_bytes() == b"remove second"
    assert Path(updater.changes_file_path).is_file()
    assert source_file.read_bytes() == b"new file"
    assert not Path(updater._get_apply_complete_path()).exists()

    restarted_updater = _restart_incremental_updater(updater)
    with (
        patch.object(Updater, "terminate_processes"),
        patch("builtins.input"),
        patch("updater.subprocess.run"),
        patch("updater.subprocess.Popen"),
    ):
        assert restarted_updater.run(apply_mode=True) is None

    assert not obsolete_dir.exists()
    assert (Path(updater.cover_folder_path) / "new.txt").read_bytes() == b"new file"
    assert outside_sentinel.read_bytes() == b"keep outside install"
    assert not Path(updater.extract_folder_path).exists()
    assert not Path(updater.changes_file_path).exists()
    assert not Path(updater._get_apply_complete_path()).exists()


def test_incremental_update_recovers_after_process_exit_during_file_copy(tmp_path):
    updater = _incremental_updater(tmp_path, {"modified": ["nested/existing.txt"]})
    install_file = Path(updater.cover_folder_path) / "nested" / "existing.txt"
    install_file.parent.mkdir()
    install_file.write_bytes(b"old version")
    source_file = Path(updater.extract_folder_path) / "nested" / "existing.txt"
    source_file.parent.mkdir()
    source_file.write_bytes(b"new complete version")

    child_script = """
import os
import sys
from unittest.mock import patch

from updater import Updater

updater = object.__new__(Updater)
updater.cover_folder_path, updater.extract_folder_path, updater.changes_file_path = sys.argv[1:4]
updater.download_file_path = None

def exit_after_partial_copy(source, destination):
    with open(source, "rb") as source_file, open(destination, "wb") as destination_file:
        destination_file.write(source_file.read(4))
        destination_file.flush()
        os.fsync(destination_file.fileno())
    os._exit(73)

with patch.object(Updater, "terminate_processes"), patch(
    "updater.shutil.copy2", side_effect=exit_after_partial_copy
):
    updater.run(apply_mode=True)
"""
    project_root = Path(__file__).resolve().parents[3]
    child_environment = os.environ.copy()
    child_environment["PYTHONPATH"] = os.pathsep.join(
        filter(
            None,
            (str(project_root), child_environment.get("PYTHONPATH")),
        )
    )
    child_result = subprocess.run(
        [
            sys.executable,
            "-c",
            child_script,
            updater.cover_folder_path,
            updater.extract_folder_path,
            updater.changes_file_path,
        ],
        cwd=tmp_path,
        env=child_environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert child_result.returncode == 73, child_result.stdout + child_result.stderr
    assert install_file.read_bytes() == b"new "
    assert Path(updater.extract_folder_path).is_dir()
    assert Path(updater.changes_file_path).is_file()

    restarted_updater = _restart_incremental_updater(updater)
    with (
        patch.object(Updater, "terminate_processes"),
        patch("builtins.input"),
        patch("updater.subprocess.run"),
        patch("updater.subprocess.Popen"),
    ):
        assert restarted_updater.run(apply_mode=True) is None

    assert install_file.read_bytes() == b"new complete version"
    assert not Path(updater.extract_folder_path).exists()
    assert not Path(updater.changes_file_path).exists()


def test_full_update_recovers_after_process_exit_during_directory_copy(tmp_path):
    updater = object.__new__(Updater)
    updater.cover_folder_path = str(tmp_path / "install")
    updater.extract_folder_path = str(tmp_path / "payload" / "AALC")
    updater.changes_file_path = str(tmp_path / "changes.json")
    updater.delete_folder_path = str(Path(updater.cover_folder_path) / "assets" / "images")
    updater.download_file_path = None

    install = Path(updater.cover_folder_path)
    extracted = Path(updater.extract_folder_path)
    install.mkdir()
    (install / "assets" / "images").mkdir(parents=True)
    (Path(updater.delete_folder_path) / "old.png").write_bytes(b"old image")
    source_folder = extracted / "nested"
    source_folder.mkdir(parents=True)
    (source_folder / "first.txt").write_bytes(b"new first file")
    (source_folder / "second.txt").write_bytes(b"new second file")
    outside_sentinel = tmp_path / "outside.txt"
    outside_sentinel.write_bytes(b"keep outside install")

    child_script = """
import os
import shutil
import sys
from pathlib import Path
from unittest.mock import patch

from updater import Updater

updater = object.__new__(Updater)
updater.cover_folder_path, updater.extract_folder_path, updater.changes_file_path, updater.delete_folder_path = sys.argv[1:5]
updater.download_file_path = None

def exit_after_partial_copytree(source, destination, *args, **kwargs):
    destination = Path(destination)
    (destination / "nested").mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(source) / "nested" / "first.txt", destination / "nested" / "first.txt")
    os._exit(79)

with patch.object(Updater, "terminate_processes"), patch(
    "updater.shutil.copytree", side_effect=exit_after_partial_copytree
):
    updater.run(apply_mode=True)
"""
    project_root = Path(__file__).resolve().parents[3]
    child_environment = os.environ.copy()
    child_environment["PYTHONPATH"] = os.pathsep.join(
        filter(
            None,
            (str(project_root), child_environment.get("PYTHONPATH")),
        )
    )
    child_result = subprocess.run(
        [
            sys.executable,
            "-c",
            child_script,
            updater.cover_folder_path,
            updater.extract_folder_path,
            updater.changes_file_path,
            updater.delete_folder_path,
        ],
        cwd=tmp_path,
        env=child_environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    installed_first = install / "nested" / "first.txt"
    installed_second = install / "nested" / "second.txt"
    assert child_result.returncode == 79, child_result.stdout + child_result.stderr
    assert installed_first.read_bytes() == b"new first file"
    assert not installed_second.exists()
    assert not Path(updater.delete_folder_path).exists()
    assert extracted.is_dir()
    assert outside_sentinel.read_bytes() == b"keep outside install"

    restarted_updater = object.__new__(Updater)
    restarted_updater.cover_folder_path = updater.cover_folder_path
    restarted_updater.extract_folder_path = updater.extract_folder_path
    restarted_updater.changes_file_path = updater.changes_file_path
    restarted_updater.delete_folder_path = updater.delete_folder_path
    restarted_updater.download_file_path = None
    with (
        patch.object(Updater, "terminate_processes"),
        patch("builtins.input"),
        patch("updater.subprocess.run") as launch,
        patch("updater.subprocess.Popen"),
    ):
        launch.return_value.returncode = 0
        assert restarted_updater.run(apply_mode=True) is None

    assert installed_first.read_bytes() == b"new first file"
    assert installed_second.read_bytes() == b"new second file"
    assert not extracted.exists()
    assert not Path(updater.changes_file_path).exists()
    assert not Path(updater._get_apply_complete_path()).exists()
    assert outside_sentinel.read_bytes() == b"keep outside install"


@pytest.mark.parametrize("delete_error", [PermissionError, FileNotFoundError])
def test_full_update_fails_and_keeps_payload_when_old_resource_delete_fails(
    tmp_path, delete_error
):
    updater = object.__new__(Updater)
    updater.cover_folder_path = str(tmp_path / "install")
    updater.extract_folder_path = str(tmp_path / "payload" / "AALC")
    updater.changes_file_path = str(tmp_path / "changes.json")
    updater.delete_folder_path = str(Path(updater.cover_folder_path) / "assets" / "images")
    updater.download_file_path = str(tmp_path / "AALC.7z")

    extracted = Path(updater.extract_folder_path)
    old_resources = Path(updater.delete_folder_path)
    old_resources.mkdir(parents=True)
    first_old_resource = old_resources / "first.png"
    second_old_resource = old_resources / "second.png"
    first_old_resource.write_bytes(b"old first image")
    second_old_resource.write_bytes(b"old second image")
    new_resource = extracted / "assets" / "images" / "new.png"
    new_resource.parent.mkdir(parents=True)
    new_resource.write_bytes(b"new image")
    archive = Path(updater.download_file_path)
    archive.write_bytes(b"update archive")
    outside_sentinel = tmp_path / "outside.txt"
    outside_sentinel.write_bytes(b"keep outside install")
    real_rmtree = shutil.rmtree

    def fail_after_partial_delete(path, *args, **kwargs):
        if Path(path) == old_resources:
            first_old_resource.unlink()
            raise delete_error("old resource deletion failed")
        return real_rmtree(path, *args, **kwargs)

    with (
        patch.object(updater, "terminate_processes"),
        patch("updater.shutil.rmtree", side_effect=fail_after_partial_delete),
        patch("builtins.input") as wait_for_exit,
        patch("updater.subprocess.run") as launch,
        patch("updater.subprocess.Popen") as launch_fallback,
    ):
        result = updater.run(apply_mode=True)

    assert result is False
    assert not first_old_resource.exists()
    assert second_old_resource.read_bytes() == b"old second image"
    assert not (old_resources / "new.png").exists()
    assert new_resource.read_bytes() == b"new image"
    assert archive.read_bytes() == b"update archive"
    assert extracted.is_dir()
    assert not Path(updater._get_apply_complete_path()).exists()
    assert outside_sentinel.read_bytes() == b"keep outside install"
    wait_for_exit.assert_not_called()
    launch.assert_not_called()
    launch_fallback.assert_not_called()

    restarted_updater = object.__new__(Updater)
    restarted_updater.cover_folder_path = updater.cover_folder_path
    restarted_updater.extract_folder_path = updater.extract_folder_path
    restarted_updater.changes_file_path = updater.changes_file_path
    restarted_updater.delete_folder_path = updater.delete_folder_path
    restarted_updater.download_file_path = updater.download_file_path
    with (
        patch.object(restarted_updater, "terminate_processes"),
        patch("builtins.input"),
        patch("updater.subprocess.run") as retry_launch,
        patch("updater.subprocess.Popen"),
    ):
        retry_launch.return_value.returncode = 0
        assert restarted_updater.run(apply_mode=True) is None

    assert not second_old_resource.exists()
    assert (Path(updater.cover_folder_path) / "assets" / "images" / "new.png").read_bytes() == b"new image"
    assert not extracted.exists()
    assert not archive.exists()
    assert not Path(updater._get_apply_complete_path()).exists()
    assert outside_sentinel.read_bytes() == b"keep outside install"


def test_full_update_skips_missing_old_resource_directory(tmp_path):
    updater = object.__new__(Updater)
    updater.cover_folder_path = str(tmp_path / "install")
    updater.extract_folder_path = str(tmp_path / "payload" / "AALC")
    updater.changes_file_path = str(tmp_path / "changes.json")
    updater.delete_folder_path = str(Path(updater.cover_folder_path) / "assets" / "images")

    install = Path(updater.cover_folder_path)
    install.mkdir()
    new_resource = Path(updater.extract_folder_path) / "assets" / "images" / "new.png"
    new_resource.parent.mkdir(parents=True)
    new_resource.write_bytes(b"new image")
    assert not Path(updater.delete_folder_path).exists()

    updater.cover_folder()

    installed_resource = install / "assets" / "images" / "new.png"
    assert installed_resource.read_bytes() == b"new image"


def test_full_update_recovers_after_process_exit_during_old_resource_delete(tmp_path):
    updater = object.__new__(Updater)
    updater.cover_folder_path = str(tmp_path / "install")
    updater.extract_folder_path = str(tmp_path / "payload" / "AALC")
    updater.changes_file_path = str(tmp_path / "changes.json")
    updater.delete_folder_path = str(Path(updater.cover_folder_path) / "assets" / "images")
    updater.download_file_path = None

    install = Path(updater.cover_folder_path)
    extracted = Path(updater.extract_folder_path)
    old_resources = Path(updater.delete_folder_path)
    old_resources.mkdir(parents=True)
    first_old_resource = old_resources / "first.png"
    second_old_resource = old_resources / "second.png"
    first_old_resource.write_bytes(b"old first image")
    second_old_resource.write_bytes(b"old second image")
    new_resource = extracted / "assets" / "images" / "new.png"
    new_resource.parent.mkdir(parents=True)
    new_resource.write_bytes(b"new image")
    outside_sentinel = tmp_path / "outside.txt"
    outside_sentinel.write_bytes(b"keep outside install")

    child_script = """
import os
import shutil
import sys
from pathlib import Path
from unittest.mock import patch

from updater import Updater

updater = object.__new__(Updater)
updater.cover_folder_path, updater.extract_folder_path, updater.changes_file_path, updater.delete_folder_path = sys.argv[1:5]
updater.download_file_path = None
real_rmtree = shutil.rmtree

def exit_after_partial_resource_delete(path, *args, **kwargs):
    if Path(path) == Path(updater.delete_folder_path):
        (Path(path) / "first.png").unlink()
        os._exit(82)
    return real_rmtree(path, *args, **kwargs)

with patch.object(Updater, "terminate_processes"), patch(
    "updater.shutil.rmtree", side_effect=exit_after_partial_resource_delete
):
    updater.run(apply_mode=True)
"""
    project_root = Path(__file__).resolve().parents[3]
    child_environment = os.environ.copy()
    child_environment["PYTHONPATH"] = os.pathsep.join(
        filter(
            None,
            (str(project_root), child_environment.get("PYTHONPATH")),
        )
    )
    child_result = subprocess.run(
        [
            sys.executable,
            "-c",
            child_script,
            updater.cover_folder_path,
            updater.extract_folder_path,
            updater.changes_file_path,
            updater.delete_folder_path,
        ],
        cwd=tmp_path,
        env=child_environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert child_result.returncode == 82, child_result.stdout + child_result.stderr
    assert not first_old_resource.exists()
    assert second_old_resource.exists()
    assert not (install / "assets" / "images" / "new.png").exists()
    assert extracted.is_dir()
    assert outside_sentinel.read_bytes() == b"keep outside install"

    restarted_updater = object.__new__(Updater)
    restarted_updater.cover_folder_path = updater.cover_folder_path
    restarted_updater.extract_folder_path = updater.extract_folder_path
    restarted_updater.changes_file_path = updater.changes_file_path
    restarted_updater.delete_folder_path = updater.delete_folder_path
    restarted_updater.download_file_path = None
    with (
        patch.object(Updater, "terminate_processes"),
        patch("builtins.input"),
        patch("updater.subprocess.run") as launch,
        patch("updater.subprocess.Popen"),
    ):
        launch.return_value.returncode = 0
        assert restarted_updater.run(apply_mode=True) is None

    assert not second_old_resource.exists()
    assert (install / "assets" / "images" / "new.png").read_bytes() == b"new image"
    assert not extracted.exists()
    assert not Path(updater.changes_file_path).exists()
    assert not Path(updater._get_apply_complete_path()).exists()
    assert outside_sentinel.read_bytes() == b"keep outside install"


def test_incremental_update_replays_after_process_exit_before_completion_marker_sync(
    tmp_path,
):
    updater = _incremental_updater(tmp_path, {"modified": ["nested/existing.txt"]})
    install_file = Path(updater.cover_folder_path) / "nested" / "existing.txt"
    install_file.parent.mkdir()
    install_file.write_bytes(b"old version")
    source_file = Path(updater.extract_folder_path) / "nested" / "existing.txt"
    source_file.parent.mkdir()
    source_file.write_bytes(b"new complete version")

    child_script = """
import os
import sys
from unittest.mock import patch

from updater import Updater

updater = object.__new__(Updater)
updater.cover_folder_path, updater.extract_folder_path, updater.changes_file_path = sys.argv[1:4]
updater.download_file_path = None
updater.file_name = "test-update.7z"

def exit_before_marker_sync(file_descriptor):
    os._exit(76)

with patch.object(Updater, "terminate_processes"), patch(
    "updater.os.fsync", side_effect=exit_before_marker_sync
):
    updater.run(apply_mode=True)
"""
    project_root = Path(__file__).resolve().parents[3]
    child_environment = os.environ.copy()
    child_environment["PYTHONPATH"] = os.pathsep.join(
        filter(
            None,
            (str(project_root), child_environment.get("PYTHONPATH")),
        )
    )
    child_result = subprocess.run(
        [
            sys.executable,
            "-c",
            child_script,
            updater.cover_folder_path,
            updater.extract_folder_path,
            updater.changes_file_path,
        ],
        cwd=tmp_path,
        env=child_environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert child_result.returncode == 76, child_result.stdout + child_result.stderr
    assert install_file.read_bytes() == b"new complete version"
    assert source_file.read_bytes() == b"new complete version"
    assert Path(updater.changes_file_path).is_file()
    assert not Path(updater._get_apply_complete_path()).exists()
    assert Path(f"{updater._get_apply_complete_path()}.tmp").read_text(
        encoding="utf-8"
    ) == "test-update.7z"

    restarted_updater = _restart_incremental_updater(updater)
    with (
        patch.object(Updater, "terminate_processes"),
        patch("builtins.input"),
        patch("updater.subprocess.run"),
        patch("updater.subprocess.Popen"),
    ):
        assert restarted_updater.run(apply_mode=True) is None

    assert install_file.read_bytes() == b"new complete version"
    assert not Path(updater.extract_folder_path).exists()
    assert not Path(updater.changes_file_path).exists()
    assert not Path(updater._get_apply_complete_path()).exists()


def test_incremental_update_replays_after_process_exit_during_completion_marker_write(tmp_path):
    updater = _incremental_updater(tmp_path, {"modified": ["nested/existing.txt"]})
    install_file = Path(updater.cover_folder_path) / "nested" / "existing.txt"
    install_file.parent.mkdir()
    install_file.write_bytes(b"old version")
    source_file = Path(updater.extract_folder_path) / "nested" / "existing.txt"
    source_file.parent.mkdir()
    source_file.write_bytes(b"new complete version")

    child_script = """
import os
import sys
from unittest.mock import patch

from updater import Updater

updater = object.__new__(Updater)
updater.cover_folder_path, updater.extract_folder_path, updater.changes_file_path = sys.argv[1:4]
updater.download_file_path = None

def exit_before_completion_marker_replace(source, destination):
    if destination == updater._get_apply_complete_path():
        os._exit(75)
    raise AssertionError(f"Unexpected marker replacement: {source} -> {destination}")

with patch.object(Updater, "terminate_processes"), patch(
    "updater.os.replace", side_effect=exit_before_completion_marker_replace
):
    updater.run(apply_mode=True)
"""
    project_root = Path(__file__).resolve().parents[3]
    child_environment = os.environ.copy()
    child_environment["PYTHONPATH"] = os.pathsep.join(
        filter(
            None,
            (str(project_root), child_environment.get("PYTHONPATH")),
        )
    )
    child_result = subprocess.run(
        [
            sys.executable,
            "-c",
            child_script,
            updater.cover_folder_path,
            updater.extract_folder_path,
            updater.changes_file_path,
        ],
        cwd=tmp_path,
        env=child_environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert child_result.returncode == 75, child_result.stdout + child_result.stderr
    assert install_file.read_bytes() == b"new complete version"
    assert source_file.read_bytes() == b"new complete version"
    assert Path(updater.changes_file_path).is_file()
    assert not Path(updater._get_apply_complete_path()).exists()
    assert Path(f"{updater._get_apply_complete_path()}.tmp").is_file()

    restarted_updater = _restart_incremental_updater(updater)
    with (
        patch.object(Updater, "terminate_processes"),
        patch("builtins.input"),
        patch("updater.subprocess.run"),
        patch("updater.subprocess.Popen"),
    ):
        assert restarted_updater.run(apply_mode=True) is None

    assert install_file.read_bytes() == b"new complete version"
    assert not Path(updater.extract_folder_path).exists()
    assert not Path(updater.changes_file_path).exists()
    assert not Path(updater._get_apply_complete_path()).exists()


def test_run_resumes_cleanup_after_process_exit_during_payload_removal(tmp_path):
    updater = _incremental_updater(tmp_path, {"modified": ["nested/existing.txt"]})
    install_file = Path(updater.cover_folder_path) / "nested" / "existing.txt"
    install_file.parent.mkdir()
    install_file.write_bytes(b"old version")
    source_file = Path(updater.extract_folder_path) / "nested" / "existing.txt"
    source_file.parent.mkdir()
    source_file.write_bytes(b"new complete version")
    download_file = tmp_path / "payload" / "AALC.7z"
    download_file.write_bytes(b"test archive")
    updater.download_file_path = str(download_file)

    child_script = """
import os
import shutil
import sys
from pathlib import Path
from unittest.mock import patch

from updater import Updater

updater = object.__new__(Updater)
updater.cover_folder_path, updater.extract_folder_path, updater.changes_file_path = sys.argv[1:4]
updater.download_file_path = sys.argv[4]
real_rmtree = shutil.rmtree

def exit_during_payload_removal(path, *args, **kwargs):
    if Path(path) == Path(updater.extract_folder_path):
        (Path(path) / "nested" / "existing.txt").unlink()
        os._exit(74)
    return real_rmtree(path, *args, **kwargs)

with patch.object(Updater, "terminate_processes"), patch(
    "updater.shutil.rmtree", side_effect=exit_during_payload_removal
):
    updater.run(apply_mode=True)
"""
    project_root = Path(__file__).resolve().parents[3]
    child_environment = os.environ.copy()
    child_environment["PYTHONPATH"] = os.pathsep.join(
        filter(
            None,
            (str(project_root), child_environment.get("PYTHONPATH")),
        )
    )
    child_result = subprocess.run(
        [
            sys.executable,
            "-c",
            child_script,
            updater.cover_folder_path,
            updater.extract_folder_path,
            updater.changes_file_path,
            updater.download_file_path,
        ],
        cwd=tmp_path,
        env=child_environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert child_result.returncode == 74, child_result.stdout + child_result.stderr
    assert install_file.read_bytes() == b"new complete version"
    assert not download_file.exists()
    assert Path(updater.changes_file_path).is_file()
    assert not source_file.exists()
    assert Path(updater._get_apply_complete_path()).is_file()

    restarted_updater = _restart_incremental_updater(updater)
    with (
        patch.object(Updater, "terminate_processes") as terminate,
        patch("builtins.input"),
        patch("updater.subprocess.run"),
        patch("updater.subprocess.Popen"),
    ):
        assert restarted_updater.run(apply_mode=True) is None

    terminate.assert_not_called()
    assert install_file.read_bytes() == b"new complete version"
    assert not Path(updater.extract_folder_path).exists()
    assert not Path(updater.changes_file_path).exists()
    assert not Path(updater._get_apply_complete_path()).exists()


def test_new_update_cleans_previous_completion_without_deleting_new_archive(tmp_path):
    updater = _incremental_updater(tmp_path, {"modified": ["nested/existing.txt"]})
    updater.download_file_path = str(tmp_path / "payload" / "AALC.7z")
    Path(updater.download_file_path).write_bytes(b"new archive")
    marker_path = Path(updater._get_apply_complete_path())
    marker_path.write_text("AALC.7z", encoding="utf-8")

    with (
        patch.object(updater, "_prepare_update_payload") as prepare,
        patch.object(updater, "_handoff_to_new_updater", return_value=True) as handoff,
    ):
        assert updater.run(apply_mode=False) is None

    prepare.assert_called_once_with(False)
    handoff.assert_called_once_with()
    assert Path(updater.download_file_path).read_bytes() == b"new archive"
    assert not Path(updater.extract_folder_path).exists()
    assert not Path(updater.changes_file_path).exists()
    assert not marker_path.exists()


def test_run_can_retry_after_partial_incremental_delete_with_new_instance(tmp_path):
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
        patch.object(Updater, "terminate_processes") as terminate,
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

        restarted_updater = _restart_incremental_updater(updater)
        assert restarted_updater.run(apply_mode=True) is None

    assert terminate.call_count == 2
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


def test_run_can_retry_after_partial_incremental_directory_delete_with_new_instance(tmp_path):
    updater = _incremental_updater(tmp_path, {"deleted_dir": ["obsolete"]})
    updater.download_file_path = None
    obsolete_dir = Path(updater.cover_folder_path) / "obsolete"
    obsolete_dir.mkdir()
    first_file = obsolete_dir / "first.txt"
    second_file = obsolete_dir / "second.txt"
    first_file.write_bytes(b"first obsolete file")
    second_file.write_bytes(b"second obsolete file")
    sentinel = tmp_path / "outside.txt"
    sentinel.write_bytes(b"keep outside install")
    changes_file = Path(updater.changes_file_path)
    extract_folder = Path(updater.extract_folder_path)
    real_rmtree = shutil.rmtree

    def fail_after_partial_delete(path, *args, **kwargs):
        if Path(path) == obsolete_dir:
            first_file.unlink()
            raise PermissionError("directory is in use")
        return real_rmtree(path, *args, **kwargs)

    with (
        patch.object(Updater, "terminate_processes") as terminate,
        patch("builtins.input"),
        patch("updater.subprocess.run"),
        patch("updater.subprocess.Popen"),
    ):
        with patch("updater.shutil.rmtree", side_effect=fail_after_partial_delete):
            assert updater.run(apply_mode=True) is False

        assert not first_file.exists()
        assert second_file.read_bytes() == b"second obsolete file"
        assert sentinel.read_bytes() == b"keep outside install"
        assert changes_file.is_file()
        assert extract_folder.is_dir()

        restarted_updater = _restart_incremental_updater(updater)
        assert restarted_updater.run(apply_mode=True) is None

    assert terminate.call_count == 2
    assert not obsolete_dir.exists()
    assert sentinel.read_bytes() == b"keep outside install"
    assert not changes_file.exists()
    assert not extract_folder.exists()


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

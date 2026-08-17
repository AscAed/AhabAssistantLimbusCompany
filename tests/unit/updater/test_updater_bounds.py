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

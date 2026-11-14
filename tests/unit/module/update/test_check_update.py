from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import requests

from module.update.check_update import UpdateStatus, UpdateThread, update


def test_update_check_invalid_local_version_skips_network():
    thread = UpdateThread(timeout=5, flag=False)
    thread.error_msg = ""
    signals = []
    thread.updateSignal.connect(signals.append)

    with patch("module.update.check_update.cfg") as mock_cfg:
        mock_cfg.version = "DEFAULT VERSION"
        with patch.object(thread, "check_update_info_mirrorchyan") as mock_mirror:
            thread.run()

    assert signals == [UpdateStatus.FAILURE]
    assert "本地版本号无效" in thread.error_msg
    mock_mirror.assert_not_called()


def test_update_interrupted_download_preserves_existing_package(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    package_dir = tmp_path / "update_temp"
    package_dir.mkdir()
    package_path = package_dir / "AALC.zip"
    package_path.write_bytes(b"previous complete package")

    response = MagicMock()
    response.__enter__.return_value = response
    response.headers = {"content-length": "100"}

    def chunks():
        yield b"partial"
        raise requests.exceptions.ConnectionError("connection dropped")

    response.iter_content.side_effect = lambda chunk_size: chunks()
    signals = SimpleNamespace(
        update_progress=MagicMock(),
        download_progress_finished=MagicMock(),
        download_complete=MagicMock(),
        download_failed=MagicMock(),
    )
    with patch("module.update.check_update.requests.get", return_value=response):
        with patch("module.update.check_update.mediator", signals):
            update("https://example.test/AALC.zip")

    assert package_path.read_bytes() == b"previous complete package"
    assert {path.name for path in package_dir.iterdir()} == {"AALC.zip"}
    signals.download_complete.emit.assert_not_called()
    signals.download_failed.emit.assert_called_once_with(
        "下载失败，请检查网络后重试。"
    )


def test_update_commits_download_before_emitting_complete(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    response = MagicMock()
    response.__enter__.return_value = response
    response.headers = {"content-length": "8"}
    response.iter_content.side_effect = lambda chunk_size: iter([b"complete"])
    signals = SimpleNamespace(
        update_progress=MagicMock(),
        download_progress_finished=MagicMock(),
        download_complete=MagicMock(),
        download_failed=MagicMock(),
    )
    with patch("module.update.check_update.requests.get", return_value=response):
        with patch("module.update.check_update.mediator", signals):
            update("https://example.test/AALC.zip")

    package_path = tmp_path / "update_temp" / "AALC.zip"
    assert package_path.read_bytes() == b"complete"
    assert {path.name for path in package_path.parent.iterdir()} == {"AALC.zip"}
    signals.download_complete.emit.assert_called_once_with("AALC.zip")
    signals.download_failed.emit.assert_not_called()
    signals.download_progress_finished.emit.assert_not_called()


def test_update_invalid_url_emits_download_failure_without_network(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    signals = SimpleNamespace(
        update_progress=MagicMock(),
        download_progress_finished=MagicMock(),
        download_complete=MagicMock(),
        download_failed=MagicMock(),
    )
    with patch("module.update.check_update.requests.get") as get:
        with patch("module.update.check_update.mediator", signals):
            update("not a URL")

    get.assert_not_called()
    signals.download_failed.emit.assert_called_once_with("更新失败：获取的URL无效。")


def test_update_file_error_emits_download_failure_and_preserves_package(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    package_dir = tmp_path / "update_temp"
    package_dir.mkdir()
    package_path = package_dir / "AALC.zip"
    package_path.write_bytes(b"previous complete package")
    signals = SimpleNamespace(
        update_progress=MagicMock(),
        download_progress_finished=MagicMock(),
        download_complete=MagicMock(),
        download_failed=MagicMock(),
    )
    response = MagicMock()
    response.__enter__.return_value = response
    response.headers = {"content-length": "8"}
    with patch(
        "module.update.check_update.tempfile.NamedTemporaryFile",
        side_effect=OSError("disk full"),
    ):
        with patch("module.update.check_update.requests.get", return_value=response):
            with patch("module.update.check_update.mediator", signals):
                update("https://example.test/AALC.zip")

    assert package_path.read_bytes() == b"previous complete package"
    signals.download_complete.emit.assert_not_called()
    signals.download_failed.emit.assert_called_once_with(
        "更新文件保存失败，请检查磁盘空间和权限。"
    )


def test_update_ocr_unpack_error_emits_download_failure(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    response = MagicMock()
    response.__enter__.return_value = response
    response.headers = {"content-length": "8"}
    response.iter_content.side_effect = lambda chunk_size: iter([b"complete"])
    signals = SimpleNamespace(
        update_progress=MagicMock(),
        download_progress_finished=MagicMock(),
        download_complete=MagicMock(),
        download_failed=MagicMock(),
    )
    with patch("module.update.check_update.requests.get", return_value=response):
        with patch(
            "module.update.check_update.subprocess.run",
            side_effect=RuntimeError("extract failed"),
        ):
            with patch("module.update.check_update.mediator", signals):
                result = update("https://example.test/OCR.7z")

    assert result is False
    assert (tmp_path / "update_temp" / "OCR.7z").read_bytes() == b"complete"
    signals.download_complete.emit.assert_not_called()
    signals.download_failed.emit.assert_called_once_with(
        "OCR 文件解压失败，请重新下载后重试。"
    )


def test_update_ocr_unpack_success_finishes_progress(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    response = MagicMock()
    response.__enter__.return_value = response
    response.headers = {"content-length": "8"}
    response.iter_content.side_effect = lambda chunk_size: iter([b"complete"])
    signals = SimpleNamespace(
        update_progress=MagicMock(),
        download_progress_finished=MagicMock(),
        download_complete=MagicMock(),
        download_failed=MagicMock(),
    )
    with patch("module.update.check_update.requests.get", return_value=response):
        with patch("module.update.check_update.safe_unpack_archive") as unpack:
            with patch("module.update.check_update.mediator", signals):
                result = update("https://example.test/OCR.7z")

    assert result is True
    unpack.assert_called_once()
    signals.download_progress_finished.emit.assert_called_once_with()
    signals.download_failed.emit.assert_not_called()

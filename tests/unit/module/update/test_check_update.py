from unittest.mock import patch

from module.update.check_update import UpdateStatus, UpdateThread


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

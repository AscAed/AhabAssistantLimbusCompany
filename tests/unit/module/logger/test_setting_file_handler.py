from unittest.mock import patch

import pytest

from module.logger import my_log


@pytest.mark.parametrize(
    ("config_text", "expected_fragments"),
    [
        (
            "\n".join(
                [
                    "config_version: 123",
                    "set_win_size: 1080",
                    "screenshot_interval: 0.85",
                    "mouse_action_interval: 0.5",
                    "mirrorchyan_cdk: sensitive-test-cdk",
                    "team_code: sensitive-test-team",
                    "",
                ]
            ),
            ("test-version", "配置文件版本: 123", "游戏分辨率: 1080"),
        ),
        (
            "mirrorchyan_cdk: sensitive-test-cdk\ninvalid: [\n",
            ("读取配置摘要失败",),
        ),
    ],
)
def test_new_log_file_does_not_include_config_values(
    tmp_path, config_text, expected_fragments
):
    version_path = tmp_path / "version.txt"
    config_path = tmp_path / "config.yaml"
    log_path = tmp_path / "debugLog.log"
    version_path.write_text("test-version", encoding="utf-8")
    config_path.write_text(config_text, encoding="utf-8")

    with (
        patch.object(my_log, "VERSION_PATH", version_path),
        patch.object(my_log, "CONFIG_PATH", config_path),
    ):
        handler = my_log.SettingConcurrentRotatingFileHandler(
            str(log_path), maxBytes=1024 * 1024, backupCount=1, encoding="utf-8"
        )
        stream = handler.do_open()
        stream.close()
        handler.close()

    log_text = log_path.read_text(encoding="utf-8")

    for expected_fragment in expected_fragments:
        assert expected_fragment in log_text
    assert "sensitive-test-cdk" not in log_text
    assert "sensitive-test-team" not in log_text
    assert "mirrorchyan_cdk" not in log_text
    assert "详细内容:" not in log_text

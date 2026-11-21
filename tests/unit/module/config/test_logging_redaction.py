from types import SimpleNamespace
from unittest.mock import patch

from module.config.config import Config, log


def test_unsaved_set_value_redacts_cdk_from_debug_log():
    config = object.__new__(Config)
    config.config = SimpleNamespace()

    with patch.object(log, "debug") as debug_log:
        config.unsaved_set_value("mirrorchyan_cdk", "sensitive-test-cdk")

    assert config.config.mirrorchyan_cdk == "sensitive-test-cdk"
    debug_log.assert_called_once_with(
        "mirrorchyan_cdk change to: 已加密", stacklevel=2
    )

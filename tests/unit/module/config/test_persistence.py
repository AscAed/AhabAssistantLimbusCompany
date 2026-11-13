import threading
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from module.config.config import Config


def _config(tmp_path):
    config = object.__new__(Config)
    config._lock = threading.RLock()
    config._write_lock = threading.RLock()
    config._writer_idle = threading.Condition(config._lock)
    config._writer_active = False
    config._writer_event = threading.Event()
    config._pending_save = False
    config._save_timer = None
    config.config_path = tmp_path / "settings.yaml"
    config.config = SimpleNamespace(model_dump=Mock(return_value={"setting": "new"}))
    config._load_default_config = Mock(return_value={})
    config.yaml = SimpleNamespace(
        dump=Mock(side_effect=lambda data, stream: stream.write("setting: new\n"))
    )
    return config


def test_save_config_preserves_existing_file_when_serialization_fails(tmp_path):
    config = _config(tmp_path)
    config.config_path.write_text("setting: old\n", encoding="utf-8")

    def dump_partial_then_fail(_data, stream):
        stream.write("setting: par")
        raise OSError("serialization failed")

    config.yaml.dump = dump_partial_then_fail

    with pytest.raises(OSError, match="serialization failed"):
        config._save_config()

    assert config.config_path.read_text(encoding="utf-8") == "setting: old\n"
    assert list(tmp_path.glob(".settings.yaml.*.tmp")) == []


def test_save_config_preserves_existing_file_when_replace_fails(tmp_path):
    config = _config(tmp_path)
    config.config_path.write_text("setting: old\n", encoding="utf-8")

    with patch(
        "module.config.config.os.replace", side_effect=PermissionError("file is locked")
    ):
        with pytest.raises(PermissionError, match="file is locked"):
            config._save_config()

    assert config.config_path.read_text(encoding="utf-8") == "setting: old\n"
    assert list(tmp_path.glob(".settings.yaml.*.tmp")) == []


def test_load_config_closes_reader_before_saving(tmp_path):
    config = _config(tmp_path)
    config.config_path.write_text("config_version: 1\n", encoding="utf-8")
    config.backup_path = tmp_path / "backup"
    config._defaults = {}
    config.config = SimpleNamespace(config_version=1)
    reader = []
    config.yaml = SimpleNamespace(
        load=Mock(
            side_effect=lambda stream: (
                reader.append(stream)
                or {
                    "config_version": 1,
                    "operation_mode": "foreground_mouse",
                    "teams_active_queue": [],
                }
            )
        )
    )
    config._normalize_team_queue = Mock(return_value=[])
    config._sync_legacy_team_state = Mock()
    config.backup_config = Mock(side_effect=lambda: reader_is_closed(reader))
    config._save_config = Mock()

    with patch(
        "module.config.config.ConfigModel",
        return_value=SimpleNamespace(config_version=1),
    ):
        config._load_config()

    config._save_config.assert_called_once_with()


def reader_is_closed(reader):
    assert reader and reader[0].closed


def test_flush_writes_a_save_already_queued_by_the_timer(tmp_path):
    config = _config(tmp_path)
    config._writer_event.set()
    config._save_config = Mock()

    config.flush()

    config._save_config.assert_called_once_with()
    assert not config._writer_event.is_set()


def test_failed_background_write_remains_pending_for_retry(tmp_path):
    config = _config(tmp_path)
    config._writer_event.set()
    config._save_config = Mock(side_effect=OSError("disk full"))

    with patch("module.config.config.log.error"):
        config._write_queued_save()

    assert config._pending_save is True
    assert not config._writer_event.is_set()
    assert config._writer_active is False


def test_flush_waits_for_a_background_write_in_progress(tmp_path):
    config = _config(tmp_path)
    config._writer_event.set()
    save_started = threading.Event()
    release_save = threading.Event()
    flush_finished = threading.Event()
    config._save_config = Mock(
        side_effect=lambda: (save_started.set(), release_save.wait(2))
    )

    writer = threading.Thread(target=config._write_queued_save)
    writer.start()
    assert save_started.wait(1)

    flusher = threading.Thread(target=lambda: (config.flush(), flush_finished.set()))
    flusher.start()
    try:
        assert not flush_finished.wait(0.05)
    finally:
        release_save.set()
        writer.join(1)
        flusher.join(1)

    assert not writer.is_alive()
    assert not flusher.is_alive()
    assert flush_finished.is_set()
    config._save_config.assert_called_once_with()


def test_flush_drains_a_save_queued_while_waiting_for_background_write(tmp_path):
    config = _config(tmp_path)
    config._writer_event.set()
    save_started = threading.Event()
    flush_waiting = threading.Event()
    release_save = threading.Event()
    flush_finished = threading.Event()
    save_calls = 0

    def save():
        nonlocal save_calls
        save_calls += 1
        if save_calls == 1:
            save_started.set()
            assert release_save.wait(1)

    config._save_config = Mock(side_effect=save)
    config._save_interval = 60
    original_wait_for = config._writer_idle.wait_for

    def wait_for(predicate, timeout=None):
        flush_waiting.set()
        return original_wait_for(predicate, timeout)

    config._writer_idle.wait_for = wait_for

    writer = threading.Thread(target=config._write_queued_save)
    writer.start()
    assert save_started.wait(1)

    flusher = threading.Thread(target=lambda: (config.flush(), flush_finished.set()))
    flusher.start()
    assert flush_waiting.wait(1)
    config._schedule_save()
    release_save.set()
    writer.join(1)
    flusher.join(1)

    assert not writer.is_alive()
    assert not flusher.is_alive()
    assert flush_finished.is_set()
    assert save_calls == 2


def test_concurrent_saves_do_not_use_yaml_writer_at_the_same_time(tmp_path):
    config = _config(tmp_path)
    first_dump_started = threading.Event()
    second_dump_started = threading.Event()
    release_first_dump = threading.Event()
    state_lock = threading.Lock()
    active_dumps = 0
    maximum_active_dumps = 0

    def dump(_data, stream):
        nonlocal active_dumps, maximum_active_dumps
        with state_lock:
            active_dumps += 1
            maximum_active_dumps = max(maximum_active_dumps, active_dumps)
            if active_dumps == 1:
                first_dump_started.set()
            else:
                second_dump_started.set()
        try:
            release_first_dump.wait(2)
            stream.write("setting: new\n")
        finally:
            with state_lock:
                active_dumps -= 1

    config.yaml.dump = dump
    first = threading.Thread(target=config._save_config)
    second = threading.Thread(target=config._save_config)
    first.start()
    assert first_dump_started.wait(1)
    second.start()
    try:
        assert not second_dump_started.wait(0.05)
    finally:
        release_first_dump.set()
        first.join(1)
        second.join(1)

    assert not first.is_alive()
    assert not second.is_alive()
    assert maximum_active_dumps == 1

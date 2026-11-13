from unittest.mock import patch

import pytest

from module.resource_sync.service import ResourceSyncService
from module.resource_sync.state import ResourceSyncState


def test_save_state_preserves_existing_file_when_replace_fails(tmp_path):
    state_path = tmp_path / "assets" / "config" / "image_resource_state.json"
    state_path.parent.mkdir(parents=True)
    previous_state = '{"last_applied_manifest_id":"previous"}\n'
    state_path.write_text(previous_state, encoding="utf-8")
    service = ResourceSyncService(
        assets_dir=tmp_path / "assets" / "images",
        state_path=state_path,
        temp_dir=tmp_path / "update_temp",
    )

    with patch("os.replace", side_effect=PermissionError("state file is locked")):
        with pytest.raises(PermissionError, match="state file is locked"):
            service.save_state(ResourceSyncState(last_applied_manifest_id="next"))

    assert state_path.read_text(encoding="utf-8") == previous_state
    assert list(state_path.parent.glob(".image_resource_state.json.*.tmp")) == []

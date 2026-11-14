import base64
import io

import pytest
from ruamel.yaml import YAML

from module.config import TeamSetting, theme_list
from module.config.team_import_export import (
    import_team_settings,
    parse_team_settings_yaml,
)
from module.config.theme_pack_import_export import (
    import_theme_pack_weight,
    import_theme_pack_weight_from_base64,
)


def test_team_settings_file_import_accepts_valid_yaml_and_rejects_unknown_tags(tmp_path):
    payload = TeamSetting().model_dump()
    payload["custom_theme_pack_weight"] = {"pack": {"gift": 2}}
    stream = io.StringIO()
    YAML().dump(payload, stream)
    valid_file = tmp_path / "team.yaml"
    valid_file.write_text(stream.getvalue(), encoding="utf-8")

    team_setting, weights, missing = import_team_settings(str(valid_file), team_num=1)

    assert team_setting is not None
    assert weights == {"pack": {"gift": 2}}
    assert missing == []
    assert parse_team_settings_yaml('{"team_number": 2}') == {"team_number": 2}

    invalid_file = tmp_path / "tagged-team.yaml"
    invalid_file.write_text("team_number: !custom 2\n", encoding="utf-8")
    team_setting, _, missing = import_team_settings(str(invalid_file), team_num=1)

    assert team_setting is None
    assert missing


@pytest.mark.parametrize("as_base64", [False, True])
def test_theme_weight_import_rejects_unknown_tags_without_overwriting_existing_file(tmp_path, monkeypatch, as_base64):
    target_file = tmp_path / "theme_weights.yaml"
    original = "# keep this note\nexisting: 1\n"
    target_file.write_text(original, encoding="utf-8")
    monkeypatch.setattr(theme_list, "build_team_weight_path", lambda _team_num: str(target_file))
    tagged_yaml = "new_weight: !custom 2\n"

    if as_base64:
        imported = import_theme_pack_weight_from_base64(
            base64.b64encode(tagged_yaml.encode("utf-8")).decode("ascii"), team_num=1
        )
    else:
        source_file = tmp_path / "tagged-theme.yaml"
        source_file.write_text(tagged_yaml, encoding="utf-8")
        imported = import_theme_pack_weight(str(source_file), team_num=1)

    assert imported is False
    assert target_file.read_text(encoding="utf-8") == original


def test_valid_theme_weight_import_merges_and_preserves_existing_comments(tmp_path, monkeypatch):
    target_file = tmp_path / "theme_weights.yaml"
    target_file.write_text("# keep this note\nexisting: 1\n", encoding="utf-8")
    monkeypatch.setattr(theme_list, "build_team_weight_path", lambda _team_num: str(target_file))
    source_file = tmp_path / "incoming-theme.yaml"
    source_file.write_text("added: 2\n", encoding="utf-8")

    assert import_theme_pack_weight(str(source_file), team_num=1) is True
    saved = target_file.read_text(encoding="utf-8")
    assert "# keep this note" in saved
    assert "existing: 1" in saved
    assert "added: 2" in saved

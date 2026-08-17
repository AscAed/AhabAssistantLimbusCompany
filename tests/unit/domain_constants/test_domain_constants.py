from app import all_sinners_name, all_systems_name
from module.domain_constants import ALL_SINNERS_NAME, ALL_SYSTEMS
from tasks import all_sinner, all_sinners_name_zh, all_systems, observe_system, system_cn_zh


def test_domain_constants_are_single_source():
    assert all_systems == ALL_SYSTEMS
    assert all_sinners_name == ALL_SINNERS_NAME
    assert all_sinner["Dante"] == 10
    assert all_sinners_name_zh[0] == "李箱"
    assert system_cn_zh["burn"] == "烧伤"
    assert observe_system[4] == "sinking"


def test_app_and_tasks_re_export_consistent_names():
    assert all_systems_name[0] == "burn"
    assert all_systems[0] == "burn"
    assert all_sinners_name[-1] == "Gregor"

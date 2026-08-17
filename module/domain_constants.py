"""Shared domain constants for sinners and systems.

This module is the single source of truth for role/system mappings that are
re-exported by both ``app`` and ``tasks``. UI-specific option dicts that are not
shared should remain in their owning modules.
"""

ALL_SINNERS_NAME = [
    "YiSang",
    "Faust",
    "DonQuixote",
    "Ryoshu",
    "Meursault",
    "HongLu",
    "Heathcliff",
    "Ishmael",
    "Rodion",
    "Sinclair",
    "Outis",
    "Gregor",
]

ALL_SINNERS_NAME_ZH = [
    "李箱",
    "浮士",
    "堂吉",
    "良秀",
    "默尔",
    "鸿璐",
    "希斯",
    "以实",
    "罗佳",
    "辛克",
    "提斯",
    "格里",
]

ALL_SINNER = {
    "YiSang": 1,
    "Faust": 2,
    "DonQuixote": 3,
    "Ryoshu": 4,
    "Meursault": 5,
    "HongLu": 6,
    "Heathcliff": 7,
    "Ishmael": 8,
    "Rodion": 9,
    "Dante": 10,
    "Sinclair": 11,
    "Outis": 12,
    "Gregor": 13,
}

ALL_SYSTEMS = {
    0: "burn",
    1: "bleed",
    2: "tremor",
    3: "rupture",
    4: "poise",
    5: "sinking",
    6: "charge",
    7: "slash",
    8: "pierce",
    9: "blunt",
}

OBSERVE_SYSTEM = ALL_SYSTEMS | {4: ALL_SYSTEMS[5], 5: ALL_SYSTEMS[4]}

SYSTEM_CN_ZH = {
    "burn": "烧伤",
    "bleed": "流血",
    "tremor": "震颤",
    "rupture": "破裂",
    "poise": "呼吸",
    "sinking": "沉沦",
    "charge": "充能",
    "slash": "斩击",
    "pierce": "突刺",
    "blunt": "打击",
}

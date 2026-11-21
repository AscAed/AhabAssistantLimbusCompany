from module.domain_constants import (
    ALL_SINNER,
    ALL_SINNERS_NAME,
    ALL_SINNERS_NAME_ZH,
    ALL_SYSTEMS,
    OBSERVE_SYSTEM,
    OPENING_EGO_GIFT_ORDERS,
    SYSTEM_CN_ZH,
)

all_systems = ALL_SYSTEMS
observe_system = OBSERVE_SYSTEM
all_sinners_name = ALL_SINNERS_NAME
all_sinners_name_zh = ALL_SINNERS_NAME_ZH
all_sinner = ALL_SINNER

start_gift = {
    index: list(order) for index, order in enumerate(OPENING_EGO_GIFT_ORDERS)
}
system_cn_zh = SYSTEM_CN_ZH

sins = {  # bgr values
    "wrath": (0, 0, 254),
    "gloom": (239, 197, 26),
    "sloth": (49, 205, 251),
    "lust": (0, 108, 254),
    "pride": (213, 75, 1),
    "gluttony": (1, 228, 146),
    "envy": (222, 1, 150),
}

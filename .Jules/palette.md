## 2024-05-19 - [Adding tooltips to dynamic PySide6 widgets]
**Learning:** PySide6/qfluentwidgets component tooltips for icon-only buttons sometimes only get assigned correctly when retranslated or require an explicit event filter for immediate visibility depending on the widget lifecycle.
**Action:** When adding icon-only buttons in PySide6 with `qfluentwidgets`, remember to explicitly set both `Qt.CursorShape.PointingHandCursor` for affordance and `ToolTipFilter` for accessible labels.
## 2024-03-24 - Qt Event Filters in Refresh Loops
**Learning:** Avoid installing event filters (like `ToolTipFilter` in `qfluentwidgets`) inside dynamic UI update loops (e.g., `_refresh_preview`). Qt appends rather than overwrites event filters, leading to memory leaks and duplicated events on the same widget.
**Action:** Always install event filters once during widget initialization (`__init__`) and only update properties (like `setToolTip()`) during dynamic refreshes.
## 2024-07-20 - [Affordance and Tooltips for Small Buttons in qfluentwidgets]
**Learning:** When adding icon-only or small buttons (like `TransparentToolButton`) in PySide6 with `qfluentwidgets`, they do not get clear hover cursor affordance or nice accessible tooltips automatically just from `setToolTip`. Qt appends event filters, so they must be installed carefully.
**Action:** Explicitly set `Qt.CursorShape.PointingHandCursor` for visual affordance, and install a `ToolTipFilter(btn, showDelay=0, position=ToolTipPosition.BOTTOM)` to render accessible, readable tooltips.
## 2024-07-21 - [Icon-Only Button Affordance in team_setting_card.py]
**Learning:** Icon-only hint buttons (like `preview_hint_button` using `ToolButton`) need a `PointingHandCursor` rather than an `ArrowCursor` to communicate to users that the element can be interacted with, especially since tooltips require hovering to discover.
**Action:** Always verify that small hint/info tool buttons have `Qt.CursorShape.PointingHandCursor` set explicitly when built using qfluentwidgets or PySide6 components.

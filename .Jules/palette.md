## 2024-05-19 - [Adding tooltips to dynamic PySide6 widgets]
**Learning:** PySide6/qfluentwidgets component tooltips for icon-only buttons sometimes only get assigned correctly when retranslated or require an explicit event filter for immediate visibility depending on the widget lifecycle.
**Action:** When adding icon-only buttons in PySide6 with `qfluentwidgets`, remember to explicitly set both `Qt.CursorShape.PointingHandCursor` for affordance and `ToolTipFilter` for accessible labels.
## 2024-03-24 - Qt Event Filters in Refresh Loops
**Learning:** Avoid installing event filters (like `ToolTipFilter` in `qfluentwidgets`) inside dynamic UI update loops (e.g., `_refresh_preview`). Qt appends rather than overwrites event filters, leading to memory leaks and duplicated events on the same widget.
**Action:** Always install event filters once during widget initialization (`__init__`) and only update properties (like `setToolTip()`) during dynamic refreshes.
## 2024-07-22 - Pointer Cursor Affordance on Action Buttons
**Learning:** PySide6 action buttons (like PushButton and DropDownPushButton) in standard QWidget layouts do not default to `Qt.CursorShape.PointingHandCursor`, which reduces interactivity affordance. Manually overriding `setCursor` on UI buttons significantly improves accessibility and intuitive use.
**Action:** Always verify small action buttons and icon buttons explicitly have pointing hand cursors when implementing new UI components in PySide6 with `qfluentwidgets`.

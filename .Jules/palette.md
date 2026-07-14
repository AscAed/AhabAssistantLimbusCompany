## 2024-05-19 - [Adding tooltips to dynamic PySide6 widgets]
**Learning:** PySide6/qfluentwidgets component tooltips for icon-only buttons sometimes only get assigned correctly when retranslated or require an explicit event filter for immediate visibility depending on the widget lifecycle.
**Action:** When adding icon-only buttons in PySide6 with `qfluentwidgets`, remember to explicitly set both `Qt.CursorShape.PointingHandCursor` for affordance and `ToolTipFilter` for accessible labels.

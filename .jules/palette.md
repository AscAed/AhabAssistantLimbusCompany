## 2025-02-12 - Improve visual affordance with TransparentToolButton and FluentIcon
**Learning:** Using `PushButton("-")` for removal actions lacks visual clarity and can feel inconsistent with modern UI practices in `qfluentwidgets`. Replacing it with `TransparentToolButton` paired with `FluentIcon.REMOVE` (`FIF.REMOVE`) significantly improves the button's visual affordance without cluttering the UI, making the negative action much clearer to the user while keeping the layout lightweight.
**Action:** When encountering icon-only text buttons (like `"-"` or `"+"`), upgrade them to `TransparentToolButton` with the appropriate `FluentIcon` for better visual communication and a cleaner look.
## 2024-07-28 - PySide6 Icon-Only Button Accessibility
**Learning:** PySide6/Qt doesn't natively expose `setToolTip()` content to screen readers as button labels like ARIA labels do in web HTML. Icon-only buttons (like `ToolButton`, `TransparentToolButton`, or `PushButton` with just an icon) require explicitly calling `setAccessibleName()` so that screen readers can announce what the button does instead of remaining silent or reading 'unlabeled button'.
**Action:** When adding icon-only buttons or buttons that rely purely on tooltips for visual explanation in PySide6 with `qfluentwidgets`, always explicitly set `setAccessibleName(self.tr("..."))` to provide an accessible label for screen readers.
## 2024-07-29 - Missing affordance on custom PySide6 action buttons
**Learning:** When adding custom buttons to standard PySide6 dialogs (like `MessageBox`), the framework does not always inherit expected affordances (like the pointing hand cursor or tooltips) that native web elements or predefined dialog actions might have. This leads to inconsistent UX where some buttons react to hover while others don't, which can be confusing for accessibility and general navigation.
**Action:** Always explicitly set `Qt.CursorShape.PointingHandCursor` and install a `ToolTipFilter` for any custom action buttons added to PyQt/PySide6 message boxes or dialogs to ensure consistent interaction patterns.

## 2025-02-12 - MessageBoxEdit UX Auto-Select & Clear Button
**Learning:** When using `MessageBoxEdit` to prompt users for text input, the default text is not auto-selected and there is no clear button, making it tedious for users to replace or clear the default value (which is the most common action). PySide6 `qfluentwidgets.LineEdit` supports both auto-selection via `selectAll()` and a clear button via `setClearButtonEnabled(True)`.
**Action:** Whenever implementing a dialog with pre-filled text input (like `MessageBoxEdit`), always call `self.lineEdit.selectAll()` and `self.lineEdit.setClearButtonEnabled(True)` to allow users to immediately overwrite or easily clear the default value, matching native desktop UX expectations.
## 2024-08-11 - Pointer cursor on CheckBox component
**Learning:** PySide6/qfluentwidgets component CheckBox sometimes lacks pointer visual affordance when intended for user interaction, especially in specific layout contexts like footers.
**Action:** When adding or checking interactive CheckBox components in PySide6 with `qfluentwidgets`, verify and explicitly set `Qt.CursorShape.PointingHandCursor` if they miss default pointing hand behavior.
## 2025-02-12 - LineEdit UX Clear Button
**Learning:** When using `LineEdit` from `qfluentwidgets` in custom widgets (like `BaseLineEdit`), the default configuration does not include a clear button. This lacks the standard, expected affordance for users to easily clear text inputs. PySide6 `qfluentwidgets.LineEdit` natively supports a clear button via `setClearButtonEnabled(True)`.
**Action:** When working with or creating components that wrap `LineEdit`, always explicitly enable the clear button by calling `setClearButtonEnabled(True)` to improve input usability and provide better UX.

## 2025-02-12 - Upgrading text buttons to icon-only buttons
**Learning:** Upgrading standard text-based buttons (like `PushButton` with text "Clear") to icon-only buttons (like `TransparentToolButton(FIF.DELETE)`) improves visual clarity and modernizes the layout. However, it introduces a risk of accessibility regressions because the text label is removed.
**Action:** When converting a text button to an icon-only button, always preserve the semantic meaning by explicitly adding `setToolTip(...)`, `setAccessibleName(...)`, and installing a `ToolTipFilter`, and ensure these properties are correctly updated during translation (e.g., in `retranslateUi`).
## 2024-08-12 - MessageBox Accessibility Enhancement
**Learning:** In standard PySide6 dialogs like `MessageBox` (and especially custom subclasses using `qfluentwidgets`), when manually creating icon-only or generic UI buttons (like the update notification `jumpButton`), `setAccessibleName` must be explicitly defined alongside `setToolTip` because screen readers do not automatically fall back to tooltips for interactive elements, resulting in a silent or uninformative tab stop.
**Action:** Always call `btn.setAccessibleName(btn.tr("..."))` concurrently with `setToolTip()` for any non-standard or text-less interactive element injected into dialog layouts.
## 2025-02-12 - Ensure Temporary Files are Deleted
**Learning:** When creating temporary mock files (like `tests/conftest.py`) to mock dependencies during isolated local Linux testing, failing to delete them before committing will introduce global mocks into the repository, breaking the test suite on native platforms (like Windows) that actually need those modules.
**Action:** Always run `rm` on any temporary mock files (e.g. `tests/conftest.py`) generated for local testing before submitting code to ensure the remote test environment is not compromised.

## 2025-02-12 - Missing Accessible Name on ObserveGiftSelectionRow ToolButton
**Learning:** In PySide6, creating icon-only tool buttons requires an explicit `setAccessibleName` for screen readers to interpret the button's action. The `ObserveGiftSelectionRow` in `app/base_combination.py` had a remove button with a tooltip but lacked an accessible name, making it invisible to screen readers.
**Action:** Always ensure that icon-only `TransparentToolButton` widgets have `setAccessibleName` called on them with a descriptive translation string.
## 2025-02-12 - MessageBox Default Buttons Affordance
**Learning:** In `qfluentwidgets`, the default `yesButton` and `cancelButton` provided by the base `MessageBox` class do not automatically use a pointing hand cursor. When creating custom dialogs by subclassing `MessageBox`, failing to explicitly set the cursor for these buttons leads to inconsistent interaction cues compared to other UI elements.
**Action:** Always explicitly set `self.yesButton.setCursor(Qt.CursorShape.PointingHandCursor)` and `self.cancelButton.setCursor(Qt.CursorShape.PointingHandCursor)` (if not hidden) in the `__init__` of any custom `MessageBox` subclass to ensure consistent visual affordance.
## 2025-02-12 - Line constraints and auto-formatters
**Learning:** When working under strict line constraints (e.g., < 50 lines for micro-UX tasks), running global auto-formatters like `ruff format .` or `ruff check --fix .` can drastically alter unrelated code across the repository, resulting in PRs with thousands of lines changed and failing the core constraints.
**Action:** When working with strict line constraints (e.g., < 50 lines), avoid running global auto-formatters across the entire repository. Instead, target only the specific files modified (e.g., `ruff format path/to/file.py`) to prevent polluting the git history with massive unrelated formatting changes.

## 2025-02-20 - [Command Injection Mitigation in Subprocess Calls]
**Vulnerability:** Subprocess command execution using string interpolation with `shell=True` exposed arbitrary command injection if properties like `self.exe_path` contained malicious payloads.
**Learning:** Python's `subprocess.run` executed with `shell=True` should be avoided when input comes from variables that might be untrusted or derived from environment artifacts. Constructing an array of arguments bypassing the shell entirely guarantees safety. In `mumu_control.py`, `enable_app_keptlive`, `disable_app_keptlive`, and `get_app_keptlive` were affected. Refactoring one subset is an anti-pattern.
**Prevention:** Always use list-based parameters for subprocess calls unless shell functionality is expressly required, and systematically audit every method implementing similar structures in a class to avoid partial patches.
## 2024-10-24 - [Avoid `shell=True` and string formatting for subprocess.run]
**Vulnerability:** Subprocess command execution using string interpolation with `shell=True` exposed arbitrary command injection if properties like `task_name` or `os.environ.get("USERNAME")` contained malicious payloads.
**Learning:** Python's `subprocess.run` executed with `shell=True` should be avoided when input comes from variables that might be untrusted or derived from environment artifacts. Constructing an array of arguments bypassing the shell entirely guarantees safety. In `utils/utils.py`, `run_cmd` and `run_as_user` were affected. Refactoring to use lists is the standard security pattern.
**Prevention:** Always use a list of arguments and leave `shell=False` (default behavior) in `subprocess.run` or `subprocess.Popen`.
## 2024-10-25 - [Avoid os.system for dynamic shell commands]
**Vulnerability:** Invoking `os.system` with a formatted string containing dynamic variables (like `pid`) is a textbook command injection vulnerability vector. If the variable is tampered with, an attacker can append arbitrary shell commands.
**Learning:** Even if the dynamic input is intended to be a safe integer (like a process ID), parsing it through a shell string with `os.system` is a bad practice. The system was relying on shell evaluation where not strictly necessary.
**Prevention:** Replace all `os.system()` invocations that accept dynamic strings with `subprocess.run()` using a structured list of arguments (e.g., `["taskkill", "/F", "/PID", str(pid)]`) and `check=False`. This completely bypasses the shell's string evaluation and guarantees arguments are passed safely to the target process.
## 2025-02-20 - [Network Request Timeout Enhancements]
**Vulnerability:** Network requests made using `requests.get()` without a `timeout` parameter can hang indefinitely if the remote server is unresponsive, leading to resource exhaustion or application lock-up.
**Learning:** Even for simple JSON fetches or file downloads, omitting the `timeout` parameter creates a Denial of Service (DoS) risk, as default behavior blocks indefinitely. This was observed in `app/announcement_board.py` and `module/automation/input_handlers/simulator/pyminitouch/utils.py`.
**Prevention:** Always specify a `timeout` (e.g., `timeout=10`) for all external network calls using the `requests` library.
## 2024-06-13 - [Missing Timeout on External Network Requests]
**Vulnerability:** External requests in automation scripts (e.g. `requests.get` in `pyminitouch/utils.py`) lack a configured `timeout` parameter, which can cause the process to hang indefinitely if the remote server fails to respond, leading to a Denial of Service.
**Learning:** In utility functions dealing with downloading payloads/files, implicit infinite timeouts are a silent risk that can completely break long-running automation pipelines.
**Prevention:** Always enforce a `timeout` argument on `requests.get`, `requests.post`, and similar networking functions.
## 2025-02-21 - [Missing Timeout on urllib.request.urlopen]
**Vulnerability:** Similar to `requests.get`, `urllib.request.urlopen()` calls without a `timeout` parameter will hang indefinitely if the remote server fails to respond, potentially causing the CI build process to deadlock.
**Learning:** This vulnerability is easy to miss when auditing third-party libraries (like `requests`), as developers might fall back on built-in standard library tools like `urllib` without realizing they share the exact same default behavior of infinite timeouts.
**Prevention:** Always explicitly define a `timeout` parameter (e.g., `timeout=10`) when using `urllib.request.urlopen` or any other built-in HTTP request function, in addition to third-party libraries.

## 2025-02-21 - [Prevent Zip Slip during Update Extraction]
**Vulnerability:** The project was using `shutil.unpack_archive` to extract zip/tar update packages downloaded over the network. In older Python versions (and sometimes without strict filters), this is susceptible to path traversal (Zip Slip), where an attacker-crafted archive containing relative paths (e.g. `../../../../malicious.exe`) can write to arbitrary locations on the file system, leading to Remote Code Execution (RCE).
**Learning:** Even built-in convenience functions like `shutil.unpack_archive` are not guaranteed to be secure against malicious payloads without appropriate filtering.
**Prevention:** To prevent Zip Slip vulnerabilities, do not use `shutil.unpack_archive` directly for untrusted archives without safe filters. Instead, manually inspect and validate the members of `zipfile.ZipFile` and `tarfile.open` to ensure that their absolute paths start with the target extraction directory's absolute path before allowing extraction.
## 2025-02-21 - [Avoid Over-Permissive chmod 777]
**Vulnerability:** Setting file permissions to `777` (read, write, execute for everyone) via `chmod` creates an over-permissive environment on Android devices. This allows any process or user on the device to tamper with or execute the pushed binaries, posing a significant security risk.
**Learning:** When pushing executables to a device using tools like ADB, it's common for developers to lazily use `chmod 777` to guarantee execution. This violates the Principle of Least Privilege and introduces a security flaw where malware could modify the executable. The issue was observed in `pyminitouch/connection.py`.
**Prevention:** Enforce the Principle of Least Privilege by using `chmod 755` (read/execute for all, write only for owner) instead of `chmod 777` when setting file permissions for executables pushed to external devices.

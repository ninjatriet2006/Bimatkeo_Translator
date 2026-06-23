# OpenAI: Security & Best Practices

## 🎯 Goal
Prevent security vulnerabilities, secrets leakage, and unsafe file execution within the AI pipeline.

## 📋 Core Directives
- **Secrets Management:** NEVER hardcode API keys, tokens, or passwords into the codebase. Always read from `.env` files, environment variables, or secure credential vaults (`os.environ.get()`).
- **Path Traversal Prevention:** When reading files based on user input, strictly sanitize file paths using `os.path.abspath()` and verify they remain within the intended `project_base_dir`.
- **Safe Deserialization:** Prefer `json.loads()` over `eval()` or `pickle.loads()`. Never execute arbitrary code or load untrusted pickles.
- **Subprocess Safety:** When using `subprocess.run()`, prefer passing arguments as a list of strings rather than `shell=True` to prevent shell injection attacks.
- **Permission Awareness:** Set appropriate file permissions when generating translation outputs or logs to prevent unauthorized modification.

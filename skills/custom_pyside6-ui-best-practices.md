# Custom: PySide6 UI/UX Best Practices

## 🎯 Goal
Ensure the Desktop UI (PySide6) remains ultra-responsive, visually premium, and completely decoupled from heavy backend processing.

## 📋 Core Directives
- **Main Thread Unblocking:** NEVER run heavy operations (LLM inferences, File I/O, OCR, network requests) on the main GUI thread. Always dispatch heavy tasks to `QThread` or use `QThreadPool` and `QRunnable`.
- **Signal/Slot Decoupling:** Use Qt's Signal and Slot mechanism extensively to pass data between background workers and the UI. Do not pass direct references of UI elements to background threads.
- **Dynamic Theming:** Adhere to modern UI aesthetics. Support Dark Mode via QSS (Qt Style Sheets) or dynamic palette updating. Do not use hardcoded RGB colors directly in the logic; load them from centralized theme configuration files.
- **Graceful Error UI:** When an error occurs in the backend, catch the signal and display a visually pleasing, non-blocking `QMessageBox` or in-app notification banner instead of crashing the app.
- **Resource Cleanup:** Override the `closeEvent` of main windows to ensure all running background `QThread` processes are signaled to quit gracefully before the application exits.

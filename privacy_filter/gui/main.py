"""Privacy Filter GUI — entry point.

Starts a local Flask server and opens a native window (pywebview)
or falls back to the system browser.
"""

import os
import sys
import socket
import threading
import argparse


def _setup_bundled_tesseract():
    """Configure PATH and TESSDATA_PREFIX for PyInstaller/AppImage bundles."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        tess_dir = os.path.join(base, "tesseract")
        if os.path.isdir(tess_dir):
            os.environ["PATH"] = tess_dir + os.pathsep + os.environ.get("PATH", "")
            tessdata = os.path.join(tess_dir, "tessdata")
            if os.path.isdir(tessdata):
                os.environ["TESSDATA_PREFIX"] = tessdata


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    _setup_bundled_tesseract()

    parser = argparse.ArgumentParser(description="Privacy Filter GUI")
    parser.add_argument("--port", type=int, default=0, help="Port (0 = auto)")
    parser.add_argument("--no-window", action="store_true", help="Skip native window, use browser only")
    args = parser.parse_args()

    port = args.port or _find_free_port()

    from privacy_filter.gui.server import create_app
    app = create_app()

    server_ready = threading.Event()

    def run_server():
        import logging
        log = logging.getLogger("werkzeug")
        log.setLevel(logging.WARNING)
        server_ready.set()
        app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)

    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    server_ready.wait(timeout=5)

    url = f"http://127.0.0.1:{port}"

    if args.no_window:
        _open_browser(url, port)
        return

    try:
        import webview
        webview.create_window(
            "Privacy Filter — TANUH DPI",
            url,
            width=1280,
            height=860,
            min_size=(900, 600),
        )
        webview.start()
    except Exception:
        _open_browser(url, port)


def _open_browser(url: str, port: int):
    import webbrowser
    webbrowser.open(url)
    print(f"Privacy Filter GUI running at {url}")
    print("Press Ctrl+C to exit.")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

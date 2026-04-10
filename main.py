import ctypes
import sys


def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def elevate():
    """Re-launch the current process with UAC elevation."""
    ctypes.windll.shell32.ShellExecuteW(
        None,           # parent window
        "runas",        # verb — triggers UAC prompt
        sys.executable, # python.exe
        " ".join(f'"{a}"' for a in sys.argv),  # args
        None,           # working dir (inherit)
        1,              # SW_SHOWNORMAL
    )


if __name__ == "__main__":
    if not is_admin():
        elevate()
        sys.exit(0)  # original process exits, elevated one takes over

    from frontend.app import app
    app.run(debug=True, host="0.0.0.0", port=8050)

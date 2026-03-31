"""VeriGen-AI CLI — Bloomberg/Grafana-style terminal dashboard."""

import sys


def main():
    try:
        from dashboard.app import VeriGenApp
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Run: pip install textual textual-plotext")
        sys.exit(1)

    try:
        app = VeriGenApp()
        app.run()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()

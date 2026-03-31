"""VeriGen-AI CLI — Bloomberg/Grafana-style terminal dashboard."""

import sys

def main():
    try:
        from dashboard.app import VeriGenApp
        app = VeriGenApp()
        app.run()
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()

"""
FINESE2 - Data Intelligence Platform
Main entry point for Flask Dashboard
"""
import argparse
import os
import sys
import webbrowser
from threading import Timer


def open_browser(port):
    """Open browser after a delay to let the server start."""
    url = f"http://127.0.0.1:{port}"
    Timer(1.5, lambda: webbrowser.open(url)).start()


def run_dashboard(host="127.0.0.1", port=5000, debug=False, open_browser_flag=True):
    """Run the Flask dashboard application."""
    # Add the dashboard directory to the path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    from dashboard.app import create_dashboard_app
    
    app = create_dashboard_app()
    
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ███████╗██╗███╗   ██╗███████╗███████╗███████╗              ║
║   ██╔════╝██║████╗  ██║██╔════╝██╔════╝██╔════╝              ║
║   █████╗  ██║██╔██╗ ██║█████╗  ███████╗█████╗                ║
║   ██╔══╝  ██║██║╚██╗██║██╔══╝  ╚════██║██╔══╝                ║
║   ██║     ██║██║ ╚████║███████╗███████║███████╗              ║
║   ╚═╝     ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝╚══════╝              ║
║                                                               ║
║   Data Intelligence Platform v3.0                             ║
║   Dashboard: http://{host}:{port}                             ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    if open_browser_flag:
        open_browser(port)
    
    app.run(host=host, port=port, debug=debug, threaded=True)


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="FINESE2 - Data Intelligence Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  py main.py dashboard                  # Start dashboard on port 5000
  py main.py dashboard --port 8080      # Start on custom port
  py main.py dashboard --no-browser     # Start without opening browser
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Start the web dashboard")
    dashboard_parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    dashboard_parser.add_argument("--port", type=int, default=5000, help="Port to bind to (default: 5000)")
    dashboard_parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    dashboard_parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    
    args = parser.parse_args()
    
    if args.command == "dashboard":
        run_dashboard(
            host=args.host,
            port=args.port,
            debug=args.debug,
            open_browser_flag=not args.no_browser
        )
    elif args.command is None:
        # Default to dashboard if no command specified
        run_dashboard()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

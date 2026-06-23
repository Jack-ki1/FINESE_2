"""
FINESE2 - Data Intelligence Platform
Main entry point for Flask Dashboard (v3.0)
"""
import argparse
import os
import sys
from app import create_app
from app.extensions import db, socketio


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description='FINESE2 - Professional Data Intelligence Platform'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default=os.environ.get('HOST', '127.0.0.1'),
        help='Host to bind the server to (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=int(os.environ.get('PORT', 5000)),
        help='Port to run the server on (default: 5000)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        default=os.environ.get('FLASK_DEBUG', '').lower() in ('true', '1', 'yes'),
        help='Enable debug mode'
    )
    
    parser.add_argument(
        '--env',
        type=str,
        choices=['development', 'production', 'testing'],
        default=os.environ.get('FLASK_ENV', 'development'),
        help='Environment configuration (default: development)'
    )

    parser.add_argument(
        '--init-db',
        action='store_true',
        default=False,
        help='Initialize database tables and exit'
    )

    args = parser.parse_args()
    
    # Set environment variables
    os.environ['FLASK_ENV'] = args.env
    
    # Create application using factory pattern
    app = create_app()

    if args.init_db:
        with app.app_context():
            try:
                db.create_all()
                print("✓ Database tables created successfully")
            except Exception as e:
                print(f"✗ Failed to create database tables: {e}")
                sys.exit(1)
        return

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
║   Dashboard: http://{args.host}:{args.port}                   ║
║   Environment: {args.env:<46s}║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Run the application with SocketIO support
    socketio.run(
        app,
        host=args.host,
        port=args.port,
        debug=args.debug,
        allow_unsafe_werkzeug=True
    )


if __name__ == '__main__':
    main()

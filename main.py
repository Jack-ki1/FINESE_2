"""
FINESE2 - Main Application Entry Point
Professional data intelligence platform with authentication and MLOps
"""
import argparse
import os
import sys
import atexit
import shutil
from app import create_app


def cleanup_temp_files():
    """Clean up any temporary files created during runtime"""
    # Clean up __pycache__ directories only within the project
    for root, dirs, files in os.walk('.', topdown=False):
        for name in dirs:
            if name == '__pycache__':
                dir_path = os.path.join(root, name)
                try:
                    shutil.rmtree(dir_path)
                except Exception as e:
                    print(f"Warning: Could not remove {dir_path}: {e}")


def main():
    """
    Main application entry point.
    
    Supports command-line arguments for host, port, and debug mode.
    """
    # Register cleanup function to run at exit
    atexit.register(cleanup_temp_files)
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='FINESE2 - Data Intelligence Platform')
    parser.add_argument('--host', default='0.0.0.0', help='Host address (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='Port number (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    # Set environment variables
    os.environ['FLASK_ENV'] = 'development' if args.debug else 'production'
    os.environ['FLASK_DEBUG'] = '1' if args.debug else '0'
    
    # Prevent creation of __pycache__ directories
    os.environ['PYTHONPYCACHEPREFIX'] = os.path.join(os.getcwd(), 'temp', 'pycache')

    # Import Flask app after setting up environment
    app = create_app()

    # Log startup information
    print(f"\n{'='*60}")
    print("FINESE2 - Professional Data Intelligence Platform")
    print(f"Version: 4.0.0")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Debug: {args.debug}")
    print(f"{'='*60}")
    
    # Run the application
    try:
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\nShutting down FINESE2...")
        cleanup_temp_files()  # Cleanup on shutdown
        sys.exit(0)
    except Exception as e:
        print(f"Error starting FINESE2: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
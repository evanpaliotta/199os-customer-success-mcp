#!/Library/Frameworks/Python.framework/Versions/3.11/bin/python3
"""
Hot-reload development wrapper for 199OS Customer Success MCP Server.
Watches for file changes and automatically reloads the server.

CRITICAL FIXES:
1. Explicit shebang with full Python 3.11 path
2. Proper subprocess management with process groups
3. Race condition fix for restarting flag
4. Debounce mechanism to prevent rapid restarts
5. Graceful shutdown with SIGTERM
6. Error handling for missing directories
7. Proper cleanup on exit
8. Thread-safe process management
"""

import sys
import os
import time
import subprocess
import signal
import threading
from pathlib import Path
from typing import Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Constants
PYTHON_EXECUTABLE = "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3"
DEBOUNCE_SECONDS = 0.5
SHUTDOWN_TIMEOUT = 5
WATCH_DIRECTORY = "./src"


class ServerReloadHandler(FileSystemEventHandler):
    """Handler for file system events with improved process management."""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.restarting = False
        self.restart_lock = threading.Lock()
        self.last_restart_time = 0
        self.output_thread: Optional[threading.Thread] = None
        self.should_stop = False
        self.start_server()

    def start_server(self) -> None:
        """Start the server process with proper error handling."""
        with self.restart_lock:
            # Debounce: prevent restarts within DEBOUNCE_SECONDS
            current_time = time.time()
            if current_time - self.last_restart_time < DEBOUNCE_SECONDS:
                return

            if self.restarting:
                return

            self.restarting = True

            # Stop existing process
            if self.process:
                print("\n🔄 Stopping server...")
                self._stop_process()

            # Start new process
            print("🚀 Starting 199OS Customer Success MCP Server with hot reload enabled...")
            print(f"📝 Watching for changes in {WATCH_DIRECTORY}")
            print("📍 Using Python:", PYTHON_EXECUTABLE)
            print("Press Ctrl+C to stop\n")

            try:
                # Use the explicit Python 3.11 interpreter
                self.process = subprocess.Popen(
                    [PYTHON_EXECUTABLE, "-u", "server.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    # Create new process group for clean shutdown
                    start_new_session=True,
                    # Ensure proper environment
                    env={**os.environ, "PYTHONUNBUFFERED": "1"}
                )

                self.last_restart_time = current_time
                print(f"✅ Server started with PID: {self.process.pid}\n")

            except Exception as e:
                print(f"❌ Failed to start server: {e}")
                self.process = None
            finally:
                self.restarting = False

    def _stop_process(self) -> None:
        """Stop the server process gracefully."""
        if not self.process:
            return

        try:
            # Try graceful shutdown first
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
                print("✅ Server stopped gracefully")
            except subprocess.TimeoutExpired:
                print("⚠️  Server didn't stop, forcing kill...")
                self.process.kill()
                self.process.wait()
                print("✅ Server killed")
        except Exception as e:
            print(f"⚠️  Error stopping process: {e}")
        finally:
            self.process = None

    def on_modified(self, event):
        """Handle file modification events."""
        # Only trigger on Python file changes
        if event.src_path.endswith('.py') and not event.is_directory:
            try:
                rel_path = Path(event.src_path).relative_to(Path.cwd())
                print(f"\n📝 File changed: {rel_path}")
                # Small delay to ensure file is fully written
                time.sleep(0.1)
                self.start_server()
            except Exception as e:
                print(f"⚠️  Error handling file change: {e}")

    def cleanup(self) -> None:
        """Clean up resources."""
        self.should_stop = True
        self._stop_process()


def verify_environment() -> bool:
    """Verify the environment is properly set up."""
    print("🔍 Verifying environment...")

    # Check Python version
    if not Path(PYTHON_EXECUTABLE).exists():
        print(f"❌ Python 3.11 not found at: {PYTHON_EXECUTABLE}")
        return False
    print(f"✅ Python 3.11 found: {PYTHON_EXECUTABLE}")

    # Check server.py exists
    if not Path("server.py").exists():
        print("❌ server.py not found in current directory")
        return False
    print("✅ server.py found")

    # Check src directory exists
    if not Path(WATCH_DIRECTORY).exists():
        print(f"❌ Watch directory not found: {WATCH_DIRECTORY}")
        return False
    print(f"✅ Watch directory found: {WATCH_DIRECTORY}")

    # Check watchdog is installed
    try:
        import watchdog
        print(f"✅ watchdog installed: {watchdog.__version__}")
    except ImportError:
        print("❌ watchdog not installed. Install with: pip install watchdog")
        return False

    print("✅ Environment verification complete\n")
    return True


def signal_handler(sig, frame, handler: ServerReloadHandler, observer: Observer):
    """Handle shutdown signals."""
    print("\n\n🛑 Shutting down...")
    observer.stop()
    handler.cleanup()
    sys.exit(0)


def print_server_output(handler: ServerReloadHandler) -> None:
    """Print server output in real-time."""
    while not handler.should_stop:
        try:
            if handler.process and handler.process.poll() is None:
                line = handler.process.stdout.readline()
                if line:
                    print(line, end='', flush=True)
            else:
                time.sleep(0.1)
        except Exception as e:
            if not handler.should_stop:
                print(f"⚠️  Error reading output: {e}")
            break


def main():
    """Main entry point."""
    # Verify environment before starting
    if not verify_environment():
        sys.exit(1)

    # Create handler and observer
    handler = ServerReloadHandler()
    observer = Observer()

    # Watch the src directory for changes
    try:
        observer.schedule(handler, path=WATCH_DIRECTORY, recursive=True)
        observer.start()
        print(f"👀 Watching {WATCH_DIRECTORY} for changes...\n")
    except Exception as e:
        print(f"❌ Failed to start file watcher: {e}")
        handler.cleanup()
        sys.exit(1)

    # Set up signal handlers
    signal.signal(
        signal.SIGINT,
        lambda sig, frame: signal_handler(sig, frame, handler, observer)
    )
    signal.signal(
        signal.SIGTERM,
        lambda sig, frame: signal_handler(sig, frame, handler, observer)
    )

    try:
        # Keep printing server output
        print_server_output(handler)
    except KeyboardInterrupt:
        signal_handler(None, None, handler, observer)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        observer.stop()
        observer.join()
        handler.cleanup()


if __name__ == "__main__":
    main()

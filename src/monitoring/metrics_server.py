"""
Prometheus Metrics HTTP Server
Serves metrics on /metrics endpoint for Prometheus scraping
"""

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)

# Import metrics handler
from src.monitoring.performance_monitor import metrics_handler, PROMETHEUS_AVAILABLE


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Prometheus metrics endpoint"""

    def do_GET(self) -> Any:
        """Handle GET requests"""
        if self.path == '/metrics':
            self.serve_metrics()
        elif self.path == '/health':
            self.serve_health()
        else:
            self.send_error(404, "Not Found")

    def serve_metrics(self) -> Any:
        """Serve Prometheus metrics"""
        try:
            if not PROMETHEUS_AVAILABLE:
                self.send_response(503)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"Prometheus client not installed\n")
                return

            # Generate metrics
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            metrics_data, content_type = loop.run_until_complete(metrics_handler.handle_metrics())
            loop.close()

            # Send response
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            self.wfile.write(metrics_data)

        except Exception as e:
            logger.error("Failed to serve metrics", error=str(e))
            self.send_error(500, "Internal Server Error")

    def serve_health(self) -> Any:
        """Serve simple health check"""
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"OK\n")

    def log_message(self, format, *args) -> Any:
        """Override to use structlog"""
        logger.debug("HTTP request", message=format % args)


class MetricsServer:
    """Metrics HTTP server manager"""

    def __init__(self, port: int = 9090, host: str = '0.0.0.0') -> Any:
        self.port = port
        self.host = host
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None

    def start(self) -> Any:
        """Start metrics server in background thread"""
        if not PROMETHEUS_AVAILABLE:
            logger.warning(
                "Prometheus client not installed. Metrics server not started. "
                "Install with: pip install prometheus-client"
            )
            return

        try:
            self.server = HTTPServer((self.host, self.port), MetricsHandler)
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()

            logger.info(
                "Metrics server started",
                host=self.host,
                port=self.port,
                metrics_url=f"http://{self.host}:{self.port}/metrics",
                health_url=f"http://{self.host}:{self.port}/health"
            )

        except Exception as e:
            logger.error("Failed to start metrics server", error=str(e))

    def stop(self) -> Any:
        """Stop metrics server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("Metrics server stopped")


# Global metrics server instance
_metrics_server: Optional[MetricsServer] = None


def get_metrics_server(port: int = 9090, host: str = '0.0.0.0') -> MetricsServer:
    """Get or create global metrics server instance"""
    global _metrics_server

    if _metrics_server is None:
        _metrics_server = MetricsServer(port=port, host=host)

    return _metrics_server


def start_metrics_server(port: int = 9090, host: str = '0.0.0.0') -> Any:
    """Start the global metrics server"""
    server = get_metrics_server(port=port, host=host)
    server.start()


def stop_metrics_server() -> Any:
    """Stop the global metrics server"""
    global _metrics_server
    if _metrics_server:
        _metrics_server.stop()

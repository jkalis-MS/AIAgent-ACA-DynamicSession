"""Chart URL helpers. Charts are served as static files by the main app at /charts."""
import os
import logging

logger = logging.getLogger(__name__)

CHART_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'charts')


def _get_base_url() -> str:
    """Build the app's public base URL from environment."""
    # Azure Container Apps: build stable ingress FQDN (not revision-specific)
    app_name = os.getenv('CONTAINER_APP_NAME')
    dns_suffix = os.getenv('CONTAINER_APP_ENV_DNS_SUFFIX')
    if app_name and dns_suffix:
        return f"https://{app_name}.{dns_suffix}"
    # Local dev fallback
    host = os.getenv('HOST', '0.0.0.0')
    port = os.getenv('PORT', '80')
    if host == '0.0.0.0':
        host = 'localhost'
    return f"http://{host}:{port}"


def ensure_chart_server() -> None:
    """No-op — charts are now served by the main app's static file mount."""
    os.makedirs(CHART_DIR, exist_ok=True)


def get_chart_url(filename: str) -> str:
    """Return the full absolute URL for a chart image."""
    return f"{_get_base_url()}/charts/{filename}"

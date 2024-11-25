import os

USE_TLS = os.environ.get("USE_TLS", "false").lower() == "true"
PUBLIC_PROTOCOL = "https" if USE_TLS else "http"

IS_PROD = os.environ.get("MODE", "PRODUCTION") != "DEVELOPMENT"

PUBLIC_WEBSITE_HOST = os.environ.get("PUBLIC_WEBSITE_HOST", "")
PUBLIC_URL = os.environ.get("PUBLIC_URL", "")

import os

USE_TLS = os.environ.get("USE_TLS", "false").lower() == "true"
PUBLIC_PROTOCOL = "https" if USE_TLS else "http"

IS_PROD = os.environ.get("MODE", "PRODUCTION") != "DEVELOPMENT"

PUBLIC_WEBSITE_HOST = os.environ.get("PUBLIC_WEBSITE_HOST", "")
PUBLIC_URL = os.environ.get("PUBLIC_URL", "")

# Secret key for hashing user passwords
PASSWORD_HASH_SECRET_KEY = os.environ.get("USERS_PASSWORD_HASH_SECRET_KEY").encode(
    "utf-8"
)

# JWT details
JWT_SECRET_KEY = os.environ.get("TOKEN_HASH_SECRET")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 2

# Minimum length requirement for user passwords
PASSWORD_MIN_LENGTH = 8

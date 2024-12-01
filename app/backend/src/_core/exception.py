from fastapi import HTTPException, status


class InvalidTokenException(HTTPException):
    """Custom exception to handle invalid tokens with an appropriate header for authentication challenges"""

    def __init__(self, detail: str = None):
        super().__init__(
            detail=detail or "Could not validate token",
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={
                "WWW-Authenticate": "Bearer error='invalid_token'"
            },  # The client can use this header to know that the token is invalid
        )

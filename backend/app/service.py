import os
import secrets

from fastapi import Header, HTTPException, status


ADMIN_KEY = os.getenv("ADMIN_KEY")


def require_admin(
    x_admin_key: str = Header(default="")
):
    if not ADMIN_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin access has not been configured."
        )

    if not secrets.compare_digest(x_admin_key, ADMIN_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials."
        )

    return True

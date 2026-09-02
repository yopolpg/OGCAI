import re
import os
import logging
from pathlib import Path
from typing import Union
# pyrefly: ignore [missing-import]
from fastapi import Request, Response
# pyrefly: ignore [missing-import]
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

logger = logging.getLogger("ogcai.security")

def validate_filename(filename: str) -> str:
    """
    Sanitize and validate uploaded filename to prevent directory traversal and null-byte injection.
    """
    # Remove path separators and null characters
    clean_name = os.path.basename(filename).replace("\x00", "").strip()
    # Remove dangerous characters
    clean_name = re.sub(r'[\\/:*?"<>|]', '_', clean_name)
    if not clean_name:
        raise ValueError("Invalid filename: Filename cannot be empty or solely special characters.")
    return clean_name

def safe_path_resolve(base_dir: Path, relative_path: Union[str, Path]) -> Path:
    """
    Safely resolve a target path strictly within an allowed base directory.
    Raises ValueError if a path traversal attempt is detected.
    """
    base_dir_resolved = base_dir.resolve()
    target_path = (base_dir_resolved / relative_path).resolve()

    # Check if target is strictly within base_dir
    try:
        target_path.relative_to(base_dir_resolved)
    except ValueError:
        logger.warning(f"Security Alert: Path traversal attempt blocked! (Target: {target_path}, Base: {base_dir_resolved})")
        raise ValueError(f"Security Violation: Access denied outside allowed directory '{base_dir.name}'.")

    return target_path

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Inject hardened HTTP Security Headers into all responses.
    """
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

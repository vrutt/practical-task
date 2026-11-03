"""Login rate limiting using the client address supplied by the ASGI server."""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

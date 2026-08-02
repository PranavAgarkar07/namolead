import hashlib

from django.conf import settings


def hash_ip(request):
    ip = request.META.get("REMOTE_ADDR", "")
    if not ip:
        return ""
    return hashlib.sha256(f"{settings.IP_HASH_SALT}:{ip}".encode()).hexdigest()

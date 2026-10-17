"""Legacy import facade; ORM declarations live in infrastructure.models."""

from apps.users.infrastructure.models import CustomUserManager, Profile, User

__all__ = ["CustomUserManager", "Profile", "User"]

"""Puertos externos usados por la aplicación de usuarios."""

from __future__ import annotations

from typing import Protocol


class ExternalAuthenticator(Protocol):
    """Adaptador para validar credenciales del proveedor externo."""

    def authenticate(self, credential: str) -> tuple[int, str] | None: ...

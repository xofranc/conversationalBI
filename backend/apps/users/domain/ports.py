"""Contratos estructurales para autenticación externa."""

from __future__ import annotations

from typing import Protocol

from .value_objects import AuthenticatedIdentity


class ExternalAuthenticator(Protocol):
    """Valida una credencial mediante un proveedor externo."""

    def authenticate(self, credential: str) -> AuthenticatedIdentity | None: ...

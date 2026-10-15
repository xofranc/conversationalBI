"""Value objects para la identidad de sesiones demo."""

from __future__ import annotations

from dataclasses import dataclass

from .exceptions import InvalidSessionIdentifier


@dataclass(frozen=True)
class SessionIdentifier:
    """Identificador opaco persistido en un campo de hasta 36 caracteres."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise InvalidSessionIdentifier("El identificador de sesión es obligatorio")
        if len(self.value) > 36:
            raise InvalidSessionIdentifier("El identificador de sesión no puede superar 36 caracteres")

    def __str__(self) -> str:
        return self.value

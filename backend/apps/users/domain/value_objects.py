"""Tipos con identidad semántica e invariantes de usuarios."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .exceptions import InvalidEmailAddress, InvalidPhoneNumber


class UserType(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


@dataclass(frozen=True)
class EmailAddress:
    """Dirección requerida; unicidad y validación de formato son del repositorio/API."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise InvalidEmailAddress("El email es obligatorio")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PhoneNumber:
    """Teléfono opcional en Profile: cuando existe son exactamente 10 dígitos."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.isdigit():
            raise InvalidPhoneNumber("El número de teléfono debe contener solo dígitos")
        if len(self.value) != 10:
            raise InvalidPhoneNumber("El número de teléfono debe tener exactamente 10 dígitos")

    def __str__(self) -> str:
        return self.value

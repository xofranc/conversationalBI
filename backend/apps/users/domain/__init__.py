"""Dominio de cuentas y perfiles; independiente de Django y del transporte."""

from .entities import Profile, User
from .exceptions import DomainError, InvalidEmailAddress, InvalidPhoneNumber
from .ports import ExternalAuthenticator
from .value_objects import AuthenticatedIdentity, EmailAddress, PhoneNumber, UserType

__all__ = [
    "DomainError",
    "EmailAddress",
    "AuthenticatedIdentity",
    "ExternalAuthenticator",
    "InvalidEmailAddress",
    "InvalidPhoneNumber",
    "PhoneNumber",
    "Profile",
    "User",
    "UserType",
]

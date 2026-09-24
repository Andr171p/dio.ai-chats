"""Объекты для определения кому принадлежит модель."""

from typing import Literal

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class SystemOwner:
    scope: Literal["system"] = "system"


@dataclass(frozen=True, slots=True)
class OrganizationOwner:
    organization_id: UUID
    scope: Literal["organization"] = "organization"


@dataclass(frozen=True, slots=True)
class UserOwner:
    organization_id: UUID
    user_id: UUID
    scope: Literal["user"] = "user"


type ConnectionOwner = SystemOwner | OrganizationOwner | UserOwner

__all__ = [
    "ConnectionOwner",
    "OrganizationOwner",
    "SystemOwner",
    "UserOwner",
]

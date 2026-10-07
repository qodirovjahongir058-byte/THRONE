from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RoleSide(StrEnum):
    """The main faction a role belongs to."""

    THRONE = "THRONE"
    BLACK = "BLACK"
    REBEL = "REBEL"
    INDEPENDENT = "INDEPENDENT"


class RoleAbilityType(StrEnum):
    """General categories of role abilities."""

    PASSIVE = "PASSIVE"
    ACTIVE = "ACTIVE"
    INFORMATION = "INFORMATION"
    PROTECTION = "PROTECTION"
    CONTROL = "CONTROL"
    ATTACK = "ATTACK"
    SPECIAL = "SPECIAL"


@dataclass(frozen=True, slots=True)
class RoleDefinition:
    """Static definition of a THRONE role."""

    key: str
    name: str
    side: RoleSide
    ability_type: RoleAbilityType
    description: str


# The complete 36-role roster will be added only after
# the final role list is confirmed.
ROLE_DEFINITIONS: dict[str, RoleDefinition] = {}


def get_role(role_key: str) -> RoleDefinition | None:
    """Return a role definition by its unique key."""
    return ROLE_DEFINITIONS.get(role_key)


def get_all_roles() -> tuple[RoleDefinition, ...]:
    """Return all registered role definitions."""
    return tuple(ROLE_DEFINITIONS.values())


def get_roles_by_side(side: RoleSide) -> tuple[RoleDefinition, ...]:
    """Return all roles belonging to a specific faction."""
    return tuple(
        role
        for role in ROLE_DEFINITIONS.values()
        if role.side == side
    )

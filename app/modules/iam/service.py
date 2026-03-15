import uuid

from sqlmodel import Session, delete, select

from app.modules.iam.models import (
    Permission,
    Role,
    RoleGrant,
    RolePermission,
    UserDataScope,
    UserRole,
)


def list_role_permissions(*, session: Session, role_id: uuid.UUID) -> list[Permission]:
    statement = (
        select(Permission)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id == role_id)
    )
    return list(session.exec(statement).all())


def list_user_roles(*, session: Session, user_id: uuid.UUID) -> list[Role]:
    statement = (
        select(Role)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
        .where(Role.status == "ACTIVE")
    )
    return list(session.exec(statement).all())


def list_user_permissions(*, session: Session, user_id: uuid.UUID) -> list[Permission]:
    statement = (
        select(Permission)
        .distinct()
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
        .where(Role.status == "ACTIVE")
    )
    return list(session.exec(statement).all())


def list_user_data_scopes(
    *, session: Session, user_id: uuid.UUID
) -> list[UserDataScope]:
    statement = select(UserDataScope).where(UserDataScope.user_id == user_id)
    return list(session.exec(statement).all())


def list_user_role_bindings(*, session: Session, user_id: uuid.UUID) -> list[UserRole]:
    statement = select(UserRole).where(UserRole.user_id == user_id)
    return list(session.exec(statement).all())


def list_role_grants_by_role(
    *, session: Session, grantor_role_id: uuid.UUID
) -> list[RoleGrant]:
    statement = select(RoleGrant).where(RoleGrant.grantor_role_id == grantor_role_id)
    return list(session.exec(statement).all())


def list_role_grants_by_user(
    *, session: Session, grantor_user_id: uuid.UUID
) -> list[RoleGrant]:
    statement = select(RoleGrant).where(RoleGrant.grantor_user_id == grantor_user_id)
    return list(session.exec(statement).all())


def list_grantee_roles_for_role(*, session: Session, role_id: uuid.UUID) -> list[Role]:
    statement = (
        select(Role)
        .join(RoleGrant, RoleGrant.grantee_role_id == Role.id)
        .where(RoleGrant.grantor_role_id == role_id)
        .order_by(Role.created_at.desc())
    )
    return list(session.exec(statement).all())


def ensure_self_role_grant(*, session: Session, role_id: uuid.UUID) -> None:
    existing = session.exec(
        select(RoleGrant)
        .where(RoleGrant.grantor_role_id == role_id)
        .where(RoleGrant.grantee_role_id == role_id)
    ).first()
    if existing:
        return
    session.add(RoleGrant(grantor_role_id=role_id, grantee_role_id=role_id))
    session.commit()


def replace_role_grants(
    *, session: Session, grantor_role_id: uuid.UUID, grantee_role_ids: list[uuid.UUID]
) -> list[RoleGrant]:
    session.exec(delete(RoleGrant).where(RoleGrant.grantor_role_id == grantor_role_id))
    session.flush()
    target_role_ids = list(dict.fromkeys([grantor_role_id, *grantee_role_ids]))
    for grantee_role_id in target_role_ids:
        session.add(
            RoleGrant(
                grantor_role_id=grantor_role_id,
                grantee_role_id=grantee_role_id,
            )
        )
    session.commit()
    return list_role_grants_by_role(session=session, grantor_role_id=grantor_role_id)


def ensure_creator_role_grant(
    *, session: Session, grantor_user_id: uuid.UUID, grantee_role_id: uuid.UUID
) -> None:
    existing = session.exec(
        select(RoleGrant)
        .where(RoleGrant.grantor_user_id == grantor_user_id)
        .where(RoleGrant.grantee_role_id == grantee_role_id)
    ).first()
    if existing:
        return
    session.add(
        RoleGrant(
            grantor_user_id=grantor_user_id,
            grantee_role_id=grantee_role_id,
        )
    )
    session.commit()


def list_visible_role_ids_for_user(
    *, session: Session, user_id: uuid.UUID, is_superuser: bool
) -> set[uuid.UUID]:
    if is_superuser:
        return {item.id for item in session.exec(select(Role)).all()}

    current_roles = list_user_roles(session=session, user_id=user_id)
    current_role_ids = {item.id for item in current_roles}
    role_grants = (
        session.exec(
            select(RoleGrant).where(RoleGrant.grantor_role_id.in_(current_role_ids))
        ).all()
        if current_role_ids
        else []
    )
    user_grants = list_role_grants_by_user(session=session, grantor_user_id=user_id)
    visible_role_ids = {
        item.grantee_role_id for item in [*role_grants, *user_grants] if item.grantee_role_id
    }
    return visible_role_ids


def list_visible_roles_for_user(
    *, session: Session, user_id: uuid.UUID, is_superuser: bool
) -> list[Role]:
    visible_role_ids = list_visible_role_ids_for_user(
        session=session, user_id=user_id, is_superuser=is_superuser
    )
    if not visible_role_ids:
        return []
    return list(
        session.exec(select(Role).where(Role.id.in_(visible_role_ids)).order_by(Role.created_at.desc())).all()
    )


def replace_user_roles(
    *, session: Session, user_id: uuid.UUID, role_ids: list[uuid.UUID]
) -> list[UserRole]:
    session.exec(delete(UserRole).where(UserRole.user_id == user_id))
    session.flush()
    for role_id in dict.fromkeys(role_ids):
        session.add(UserRole(user_id=user_id, role_id=role_id))
    session.commit()
    return list_user_role_bindings(session=session, user_id=user_id)


def list_role_permission_bindings(
    *, session: Session, role_id: uuid.UUID
) -> list[RolePermission]:
    statement = select(RolePermission).where(RolePermission.role_id == role_id)
    return list(session.exec(statement).all())


def replace_role_permissions(
    *, session: Session, role_id: uuid.UUID, permission_ids: list[uuid.UUID]
) -> list[RolePermission]:
    session.exec(delete(RolePermission).where(RolePermission.role_id == role_id))
    session.flush()
    for permission_id in dict.fromkeys(permission_ids):
        session.add(RolePermission(role_id=role_id, permission_id=permission_id))
    session.commit()
    return list_role_permission_bindings(session=session, role_id=role_id)


def replace_user_data_scopes(
    *, session: Session, user_id: uuid.UUID, scopes: list[UserDataScope]
) -> list[UserDataScope]:
    session.exec(delete(UserDataScope).where(UserDataScope.user_id == user_id))
    session.flush()
    for scope in scopes:
        session.add(scope)
    session.commit()
    return list_user_data_scopes(session=session, user_id=user_id)


def seed_permissions(*, session: Session, permission_defs: list[dict[str, str]]) -> None:
    existing_codes = set(session.exec(select(Permission.code)).all())
    for item in permission_defs:
        if item["code"] in existing_codes:
            continue
        session.add(Permission(**item))
        existing_codes.add(item["code"])
    session.commit()

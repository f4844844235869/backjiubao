import re
import uuid
from dataclasses import dataclass

from sqlmodel import Session, delete, select

from app.models import User, UserDataScope
from app.modules.employee.models import EmployeeEmploymentRecord, EmployeeProfile
from app.modules.org.models import (
    OrgNode,
    OrgNodeCreate,
    OrgNodeMemberPublic,
    UserOrgBinding,
)


def list_org_nodes(*, session: Session, store_id: uuid.UUID | None = None) -> list[OrgNode]:
    statement = select(OrgNode).order_by(OrgNode.path)
    if store_id:
        statement = statement.where(OrgNode.store_id == store_id)
    return list(session.exec(statement).all())


def create_org_node(
    *, session: Session, body: OrgNodeCreate, parent: OrgNode | None
) -> OrgNode:
    node = OrgNode(
        store_id=body.store_id,
        parent_id=body.parent_id,
        name=body.name,
        prefix=body.prefix,
        node_type=body.node_type,
        path="",
        level=parent.level + 1 if parent else 1,
        sort_order=body.sort_order,
        is_active=body.is_active,
    )
    node.path = (
        f"{parent.path}/{node.id}" if parent else f"/{body.store_id}/{node.id}"
    )
    session.add(node)
    session.commit()
    session.refresh(node)
    return node


def update_org_node(*, session: Session, node: OrgNode, data: dict) -> OrgNode:
    for key, value in data.items():
        setattr(node, key, value)
    session.add(node)
    session.commit()
    session.refresh(node)
    return node


def delete_org_node(*, session: Session, node: OrgNode) -> None:
    session.exec(delete(OrgNode).where(OrgNode.id == node.id))
    session.commit()


def list_user_org_bindings(
    *, session: Session, user_id: uuid.UUID | None = None
) -> list[UserOrgBinding]:
    statement = select(UserOrgBinding)
    if user_id:
        statement = statement.where(UserOrgBinding.user_id == user_id)
    return list(session.exec(statement).all())


def normalize_org_prefix(prefix: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]", "", prefix).upper()
    if not normalized:
        raise ValueError("ORG_PREFIX_INVALID")
    return normalized


def get_sibling_prefix_conflict(
    *,
    session: Session,
    store_id: uuid.UUID,
    parent_id: uuid.UUID | None,
    prefix: str,
    exclude_node_id: uuid.UUID | None = None,
) -> OrgNode | None:
    statement = select(OrgNode).where(
        OrgNode.store_id == store_id,
        OrgNode.parent_id == parent_id,
        OrgNode.prefix == prefix,
    )
    if exclude_node_id:
        statement = statement.where(OrgNode.id != exclude_node_id)
    return session.exec(statement).first()


def build_org_prefix_chain(*, session: Session, node: OrgNode) -> str:
    nodes = {
        item.id: item
        for item in session.exec(
            select(OrgNode).where(OrgNode.store_id == node.store_id)
        ).all()
    }
    current: OrgNode | None = node
    prefixes: list[str] = []
    while current:
        prefixes.append(current.prefix)
        current = nodes.get(current.parent_id) if current.parent_id else None
    return "".join(reversed(prefixes))


def list_org_node_members(
    *,
    session: Session,
    node: OrgNode,
    include_descendants: bool = True,
) -> tuple[list[OrgNode], list[OrgNodeMemberPublic]]:
    descendant_nodes = [node]
    if include_descendants:
        descendant_nodes = list(
            session.exec(
                select(OrgNode)
                .where(OrgNode.store_id == node.store_id)
                .where(
                    (OrgNode.id == node.id) | (OrgNode.path.startswith(f"{node.path}/"))
                )
                .order_by(OrgNode.path, OrgNode.sort_order, OrgNode.created_at)
            ).all()
        )
    descendant_node_ids = [item.id for item in descendant_nodes]
    bindings = list(
        session.exec(
            select(UserOrgBinding).where(UserOrgBinding.org_node_id.in_(descendant_node_ids))
        ).all()
    )
    if not bindings:
        return descendant_nodes, []

    users = {
        user.id: user
        for user in session.exec(
            select(User).where(User.id.in_([binding.user_id for binding in bindings]))
        ).all()
    }
    profiles = {
        profile.user_id: profile
        for profile in session.exec(
            select(EmployeeProfile).where(
                EmployeeProfile.user_id.in_([binding.user_id for binding in bindings])
            )
        ).all()
    }
    nodes_by_id = {item.id: item for item in descendant_nodes}
    from app.modules.store.models import Store

    store_record = session.get(Store, node.store_id)
    store_name = store_record.name if store_record else "未知门店"

    members: list[OrgNodeMemberPublic] = []
    for binding in bindings:
        user = users.get(binding.user_id)
        org_node = nodes_by_id.get(binding.org_node_id)
        if not user or not org_node:
            continue
        profile = profiles.get(binding.user_id)
        members.append(
            OrgNodeMemberPublic(
                user=user.model_dump(mode="json"),
                employee_no=profile.employee_no if profile else None,
                employment_status=profile.employment_status if profile else None,
                store_id=node.store_id,
                store_name=store_name,
                org_node_id=org_node.id,
                org_node_name=org_node.name,
                position_name=binding.position_name,
                is_primary=binding.is_primary,
            )
        )
    return descendant_nodes, members


def get_user_binding_in_store(
    *, session: Session, user_id: uuid.UUID, store_id: uuid.UUID
) -> UserOrgBinding | None:
    bindings = list_user_org_bindings(session=session, user_id=user_id)
    if not bindings:
        return None
    org_node_ids = [binding.org_node_id for binding in bindings]
    org_nodes = {
        node.id: node
        for node in session.exec(select(OrgNode).where(OrgNode.id.in_(org_node_ids))).all()
    }
    for binding in bindings:
        node = org_nodes.get(binding.org_node_id)
        if node and node.store_id == store_id:
            return binding
    return None


def clear_primary_binding(*, session: Session, user_id: uuid.UUID) -> None:
    existing_primary = session.exec(
        select(UserOrgBinding)
        .where(UserOrgBinding.user_id == user_id)
        .where(UserOrgBinding.is_primary.is_(True))
    ).all()
    for binding in existing_primary:
        binding.is_primary = False
        session.add(binding)


def sync_user_primary_org(
    *, session: Session, user: User, org_node: OrgNode
) -> User:
    user.primary_store_id = org_node.store_id
    user.primary_department_id = org_node.id
    session.add(user)
    return user


def switch_user_primary_store(
    *, session: Session, user: User, store_id: uuid.UUID
) -> User:
    binding = get_user_binding_in_store(session=session, user_id=user.id, store_id=store_id)
    if not binding:
        raise ValueError("USER_NOT_BOUND_TO_STORE")
    org_node = session.get(OrgNode, binding.org_node_id)
    if not org_node:
        raise ValueError("ORG_NODE_NOT_FOUND")
    clear_primary_binding(session=session, user_id=user.id)
    binding.is_primary = True
    session.add(binding)
    sync_user_primary_org(session=session, user=user, org_node=org_node)
    session.commit()
    session.refresh(user)
    return user


@dataclass(frozen=True)
class OrgNodeDeletionCheckResult:
    has_active_user_primary_refs: bool
    has_active_org_bindings: bool
    has_active_data_scopes: bool
    has_active_children: bool
    has_any_children: bool
    has_historical_user_primary_refs: bool
    has_historical_org_bindings: bool
    has_historical_data_scopes: bool
    has_employment_history: bool

    @property
    def in_use(self) -> bool:
        return any(
            [
                self.has_active_user_primary_refs,
                self.has_active_org_bindings,
                self.has_active_data_scopes,
                self.has_active_children,
            ]
        )

    @property
    def has_history(self) -> bool:
        return any(
            [
                self.has_historical_user_primary_refs,
                self.has_historical_org_bindings,
                self.has_historical_data_scopes,
                self.has_employment_history,
            ]
        )


def check_org_node_deletion_references(
    *, session: Session, node_id: uuid.UUID
) -> OrgNodeDeletionCheckResult:
    active_user_primary_ref = session.exec(
        select(User.id)
        .where(User.primary_department_id == node_id)
        .where(User.status == "ACTIVE")
    ).first()
    historical_user_primary_ref = session.exec(
        select(User.id)
        .where(User.primary_department_id == node_id)
        .where(User.status != "ACTIVE")
    ).first()
    active_org_binding = session.exec(
        select(UserOrgBinding.id)
        .join(User, User.id == UserOrgBinding.user_id)
        .where(UserOrgBinding.org_node_id == node_id)
        .where(User.status == "ACTIVE")
    ).first()
    historical_org_binding = session.exec(
        select(UserOrgBinding.id)
        .join(User, User.id == UserOrgBinding.user_id)
        .where(UserOrgBinding.org_node_id == node_id)
        .where(User.status != "ACTIVE")
    ).first()
    active_data_scope = session.exec(
        select(UserDataScope.id)
        .join(User, User.id == UserDataScope.user_id)
        .where(UserDataScope.org_node_id == node_id)
        .where(User.status == "ACTIVE")
    ).first()
    historical_data_scope = session.exec(
        select(UserDataScope.id)
        .join(User, User.id == UserDataScope.user_id)
        .where(UserDataScope.org_node_id == node_id)
        .where(User.status != "ACTIVE")
    ).first()
    active_child = session.exec(
        select(OrgNode.id)
        .where(OrgNode.parent_id == node_id)
        .where(OrgNode.is_active.is_(True))
    ).first()
    any_child = session.exec(select(OrgNode.id).where(OrgNode.parent_id == node_id)).first()
    employment_history = session.exec(
        select(EmployeeEmploymentRecord.id).where(EmployeeEmploymentRecord.org_node_id == node_id)
    ).first()

    return OrgNodeDeletionCheckResult(
        has_active_user_primary_refs=active_user_primary_ref is not None,
        has_active_org_bindings=active_org_binding is not None,
        has_active_data_scopes=active_data_scope is not None,
        has_active_children=active_child is not None,
        has_any_children=any_child is not None,
        has_historical_user_primary_refs=historical_user_primary_ref is not None,
        has_historical_org_bindings=historical_org_binding is not None,
        has_historical_data_scopes=historical_data_scope is not None,
        has_employment_history=employment_history is not None,
    )

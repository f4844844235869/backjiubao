import uuid
from dataclasses import dataclass

from sqlmodel import Session, delete, select

from app.models import User, UserDataScope
from app.modules.employee.models import EmployeeEmploymentRecord
from app.modules.org.models import OrgNode, UserOrgBinding
from app.modules.store.models import Store, StoreCreate


def list_stores(*, session: Session) -> list[Store]:
    statement = select(Store).order_by(Store.created_at.desc())
    return list(session.exec(statement).all())


def get_store_by_code(*, session: Session, code: str) -> Store | None:
    statement = select(Store).where(Store.code == code)
    return session.exec(statement).first()


def create_store(*, session: Session, body: StoreCreate) -> Store:
    store = Store.model_validate(body)
    session.add(store)
    session.commit()
    session.refresh(store)
    return store


def get_store_by_id(*, session: Session, store_id: uuid.UUID) -> Store | None:
    return session.get(Store, store_id)


def update_store(*, session: Session, store: Store, data: dict) -> Store:
    for key, value in data.items():
        setattr(store, key, value)
    session.add(store)
    session.commit()
    session.refresh(store)
    return store


def delete_store(*, session: Session, store: Store) -> None:
    session.exec(delete(Store).where(Store.id == store.id))
    session.commit()


@dataclass(frozen=True)
class StoreDeletionCheckResult:
    has_active_user_primary_refs: bool
    has_active_org_nodes: bool
    has_active_org_bindings: bool
    has_active_data_scopes: bool
    has_historical_user_primary_refs: bool
    has_historical_org_bindings: bool
    has_historical_data_scopes: bool
    has_employment_history: bool

    @property
    def in_use(self) -> bool:
        return any(
            [
                self.has_active_user_primary_refs,
                self.has_active_org_nodes,
                self.has_active_org_bindings,
                self.has_active_data_scopes,
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


def check_store_deletion_references(
    *, session: Session, store_id: uuid.UUID
) -> StoreDeletionCheckResult:
    active_user_primary_ref = session.exec(
        select(User.id)
        .where(User.primary_store_id == store_id)
        .where(User.status == "ACTIVE")
    ).first()
    historical_user_primary_ref = session.exec(
        select(User.id)
        .where(User.primary_store_id == store_id)
        .where(User.status != "ACTIVE")
    ).first()

    active_org_node = session.exec(
        select(OrgNode.id)
        .where(OrgNode.store_id == store_id)
        .where(OrgNode.is_active.is_(True))
    ).first()
    org_node_ids = session.exec(select(OrgNode.id).where(OrgNode.store_id == store_id)).all()

    active_org_binding = None
    historical_org_binding = None
    if org_node_ids:
        active_org_binding = session.exec(
            select(UserOrgBinding.id)
            .join(User, User.id == UserOrgBinding.user_id)
            .where(UserOrgBinding.org_node_id.in_(org_node_ids))
            .where(User.status == "ACTIVE")
        ).first()
        historical_org_binding = session.exec(
            select(UserOrgBinding.id)
            .join(User, User.id == UserOrgBinding.user_id)
            .where(UserOrgBinding.org_node_id.in_(org_node_ids))
            .where(User.status != "ACTIVE")
        ).first()

    active_data_scope = session.exec(
        select(UserDataScope.id)
        .join(User, User.id == UserDataScope.user_id)
        .where(UserDataScope.store_id == store_id)
        .where(User.status == "ACTIVE")
    ).first()
    historical_data_scope = session.exec(
        select(UserDataScope.id)
        .join(User, User.id == UserDataScope.user_id)
        .where(UserDataScope.store_id == store_id)
        .where(User.status != "ACTIVE")
    ).first()
    employment_history = session.exec(
        select(EmployeeEmploymentRecord.id).where(EmployeeEmploymentRecord.store_id == store_id)
    ).first()

    return StoreDeletionCheckResult(
        has_active_user_primary_refs=active_user_primary_ref is not None,
        has_active_org_nodes=active_org_node is not None,
        has_active_org_bindings=active_org_binding is not None,
        has_active_data_scopes=active_data_scope is not None,
        has_historical_user_primary_refs=historical_user_primary_ref is not None,
        has_historical_org_bindings=historical_org_binding is not None,
        has_historical_data_scopes=historical_data_scope is not None,
        has_employment_history=employment_history is not None,
    )

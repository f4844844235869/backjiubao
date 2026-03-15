from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import (
    SKU,
    EmployeeEmploymentRecord,
    EmployeeProfile,
    GiftAccount,
    GiftTemplate,
    InventoryBalance,
    InventoryTransaction,
    Item,
    Member,
    MiniappAccount,
    Notification,
    Order,
    OrderItem,
    OrgNode,
    Payment,
    Permission,
    PrincipalAccount,
    Product,
    RechargePlan,
    Role,
    RoleGrant,
    RolePermission,
    ShiftHandover,
    Store,
    TransferOrder,
    User,
    UserDataScope,
    UserOrgBinding,
    UserPhoneBinding,
    UserRole,
    WalletTransaction,
    Warehouse,
)
from app.modules.product.models import Category, FundLimit
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db(session)
        yield session
        # New parallel line tables
        session.execute(delete(WalletTransaction))
        session.execute(delete(GiftAccount))
        session.execute(delete(PrincipalAccount))
        session.execute(delete(Member))
        session.execute(delete(RechargePlan))
        session.execute(delete(Payment))
        session.execute(delete(OrderItem))
        session.execute(delete(Order))
        session.execute(delete(ShiftHandover))
        session.execute(delete(InventoryTransaction))
        session.execute(delete(InventoryBalance))
        session.execute(delete(TransferOrder))
        session.execute(delete(Warehouse))
        session.execute(delete(SKU))
        session.execute(delete(Product))
        session.execute(delete(FundLimit))
        session.execute(delete(GiftTemplate))
        session.execute(delete(Category))
        # Original tables
        statement = delete(Item)
        session.execute(statement)
        statement = delete(EmployeeEmploymentRecord)
        session.execute(statement)
        statement = delete(EmployeeProfile)
        session.execute(statement)
        statement = delete(MiniappAccount)
        session.execute(statement)
        statement = delete(UserPhoneBinding)
        session.execute(statement)
        statement = delete(Notification)
        session.execute(statement)
        statement = delete(RolePermission)
        session.execute(statement)
        statement = delete(RoleGrant)
        session.execute(statement)
        statement = delete(UserRole)
        session.execute(statement)
        statement = delete(UserDataScope)
        session.execute(statement)
        statement = delete(Permission)
        session.execute(statement)
        statement = delete(Role).where(Role.code != "admin")
        session.execute(statement)
        statement = delete(UserOrgBinding)
        session.execute(statement)
        statement = delete(OrgNode)
        session.execute(statement)
        statement = delete(Store)
        session.execute(statement)
        statement = delete(User)
        statement = statement.where(User.email != settings.FIRST_SUPERUSER)
        session.execute(statement)
        session.commit()


@pytest.fixture(scope="module")
def client(db: Session) -> Generator[TestClient, None, None]:
    _ = db
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def ensure_system_seed_data(db: Session) -> Generator[None, None, None]:
    """每条测试前补齐系统种子数据，避免用例之间互相污染。"""

    init_db(db)
    yield


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    init_db(db)
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    init_db(db)
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )

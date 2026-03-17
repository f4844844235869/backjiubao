from datetime import datetime

from sqlmodel import Session, create_engine, select

from app import crud
from app.core.config import settings
from app.core.security import get_password_hash
from app.models import (
    OrgNode,
    Permission,
    Role,
    Store,
    User,
    UserCreate,
    UserDataScope,
    UserOrgBinding,
    UserStoreRole,
)
from app.models.base import get_datetime_utc
from app.modules.employee.models import EmployeeProfile
from app.modules.employee.service import (
    create_employment_record,
    ensure_employee_profile,
    get_active_employment_record_by_user_id,
    get_employee_profile_by_user_id,
    update_employee_profile,
)
from app.modules.iam.models import RoleGrant, RolePermission
from app.modules.iam.service import ensure_self_role_grant, seed_permissions
from app.modules.org.models import OrgNodeCreate
from app.modules.org.service import (
    clear_primary_binding,
    create_org_node,
    sync_user_primary_org,
)
from app.modules.store.models import StoreCreate
from app.modules.store.service import create_store, get_store_by_code

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))

ADMIN_ROLE_CODE = "admin"
SAMPLE_USER_PASSWORD = "Jiuba123!"
DEFAULT_PERMISSION_DEFS = [
    {"code": "employee.read", "name": "查看员工", "module": "employee"},
    {"code": "employee.create", "name": "新增员工", "module": "employee"},
    {"code": "employee.update", "name": "更新员工", "module": "employee"},
    {"code": "employee.leave", "name": "员工离职", "module": "employee"},
    {"code": "employee.bind_org", "name": "绑定员工组织", "module": "employee"},
    {"code": "employee.assign_role", "name": "分配员工角色", "module": "employee"},
    {"code": "employee.assign_scope", "name": "分配员工数据范围", "module": "employee"},
    {"code": "iam.user.read", "name": "查看用户", "module": "iam"},
    {"code": "iam.user.create", "name": "创建用户", "module": "iam"},
    {"code": "iam.user.update", "name": "更新用户", "module": "iam"},
    {"code": "iam.user.delete", "name": "删除用户", "module": "iam"},
    {"code": "iam.role.read", "name": "查看角色", "module": "iam"},
    {"code": "iam.role.create", "name": "创建角色", "module": "iam"},
    {"code": "iam.role.update", "name": "更新角色", "module": "iam"},
    {"code": "iam.role.delete", "name": "删除角色", "module": "iam"},
    {"code": "iam.permission.read", "name": "查看权限", "module": "iam"},
    {"code": "iam.permission.create", "name": "创建权限", "module": "iam"},
    {"code": "iam.role.assign_permission", "name": "分配角色权限", "module": "iam"},
    {"code": "iam.user.assign_role", "name": "分配用户角色", "module": "iam"},
    {"code": "iam.user.assign_scope", "name": "分配用户数据范围", "module": "iam"},
    {"code": "org.store.read", "name": "查看门店", "module": "org"},
    {"code": "org.store.create", "name": "创建门店", "module": "org"},
    {"code": "org.store.update", "name": "更新门店", "module": "org"},
    {"code": "org.store.delete", "name": "删除门店", "module": "org"},
    {"code": "org.node.read", "name": "查看组织节点", "module": "org"},
    {"code": "org.node.create", "name": "创建组织节点", "module": "org"},
    {"code": "org.node.update", "name": "更新组织节点", "module": "org"},
    {"code": "org.node.delete", "name": "删除组织节点", "module": "org"},
    {"code": "org.binding.read", "name": "查看组织绑定", "module": "org"},
    {"code": "org.binding.create", "name": "创建组织绑定", "module": "org"},
    {"code": "org.binding.update", "name": "更新组织绑定", "module": "org"},
    {"code": "product.category.read", "name": "查看商品分类", "module": "product"},
    {"code": "product.category.manage", "name": "管理商品分类", "module": "product"},
    {"code": "product.read", "name": "查看商品", "module": "product"},
    {"code": "product.manage", "name": "管理商品", "module": "product"},
]

SAMPLE_ROLE_DEFS = [
    {
        "code": "regional_manager",
        "name": "区域经理",
        "permission_codes": [
            "employee.read",
            "employee.create",
            "employee.update",
            "employee.leave",
            "employee.bind_org",
            "org.store.read",
            "org.store.update",
            "org.node.read",
            "org.node.update",
            "org.binding.read",
            "org.binding.create",
            "org.binding.update",
            "iam.user.read",
            "product.category.read",
            "product.category.manage",
            "product.read",
            "product.manage",
        ],
    },
    {
        "code": "store_manager",
        "name": "店长",
        "permission_codes": [
            "employee.read",
            "employee.create",
            "employee.update",
            "employee.bind_org",
            "org.store.read",
            "org.node.read",
            "org.binding.read",
            "org.binding.create",
            "org.binding.update",
            "product.read",
            "product.manage",
        ],
    },
    {
        "code": "shift_leader",
        "name": "值班经理",
        "permission_codes": [
            "employee.read",
            "org.store.read",
            "org.node.read",
            "org.binding.read",
            "product.read",
        ],
    },
    {
        "code": "bartender",
        "name": "调酒师",
        "permission_codes": [
            "org.store.read",
            "org.node.read",
        ],
    },
    {
        "code": "server",
        "name": "服务员",
        "permission_codes": [
            "org.store.read",
        ],
    },
]

SAMPLE_ROLE_GRANT_DEFS = {
    "regional_manager": ["regional_manager", "store_manager", "shift_leader", "bartender", "server"],
    "store_manager": ["store_manager", "shift_leader", "bartender", "server"],
    "shift_leader": ["shift_leader", "bartender", "server"],
    "bartender": ["bartender"],
    "server": ["server"],
}

SAMPLE_STORE_DEFS = [
    {
        "code": "xinghe",
        "name": "星河店",
        "org_nodes": [
            {"key": "ops", "name": "店务中心", "node_type": "DEPARTMENT", "parent": None},
            {"key": "hall", "name": "前厅组", "node_type": "TEAM", "parent": "ops"},
            {"key": "bar", "name": "吧台组", "node_type": "TEAM", "parent": "ops"},
            {"key": "security", "name": "安保组", "node_type": "TEAM", "parent": "ops"},
        ],
    },
    {
        "code": "jiangnan",
        "name": "江南店",
        "org_nodes": [
            {"key": "ops", "name": "店务中心", "node_type": "DEPARTMENT", "parent": None},
            {"key": "hall", "name": "前厅组", "node_type": "TEAM", "parent": "ops"},
            {"key": "bar", "name": "吧台组", "node_type": "TEAM", "parent": "ops"},
            {"key": "vip", "name": "VIP服务组", "node_type": "TEAM", "parent": "ops"},
        ],
    },
    {
        "code": "college",
        "name": "大学城店",
        "org_nodes": [
            {"key": "ops", "name": "店务中心", "node_type": "DEPARTMENT", "parent": None},
            {"key": "hall", "name": "前厅组", "node_type": "TEAM", "parent": "ops"},
            {"key": "bar", "name": "吧台组", "node_type": "TEAM", "parent": "ops"},
            {"key": "event", "name": "活动执行组", "node_type": "TEAM", "parent": "ops"},
        ],
    },
]

SAMPLE_EMPLOYEE_DEFS = [
    {
        "username": "regional.manager",
        "full_name": "周明轩",
        "nickname": "区域经理老周",
        "mobile": "13900001001",
        "employee_no": "R001",
        "position_name": "区域经理",
        "store_code": "xinghe",
        "org_key": "ops",
        "role_codes": ["regional_manager"],
        "scope_defs": [
            {"scope_type": "STORE", "store_code": "xinghe"},
            {"scope_type": "STORE", "store_code": "jiangnan"},
            {"scope_type": "STORE", "store_code": "college"},
        ],
        "extra_bindings": [
            {"store_code": "jiangnan", "org_key": "ops", "position_name": "区域巡店"},
            {"store_code": "college", "org_key": "ops", "position_name": "区域巡店"},
        ],
    },
    {
        "username": "xinghe.manager",
        "full_name": "林嘉豪",
        "nickname": "星河店长",
        "mobile": "13900001002",
        "employee_no": "X001",
        "position_name": "店长",
        "store_code": "xinghe",
        "org_key": "ops",
        "role_codes": ["store_manager"],
        "scope_defs": [{"scope_type": "STORE", "store_code": "xinghe"}],
    },
    {
        "username": "jiangnan.manager",
        "full_name": "许文博",
        "nickname": "江南店长",
        "mobile": "13900001003",
        "employee_no": "J001",
        "position_name": "店长",
        "store_code": "jiangnan",
        "org_key": "ops",
        "role_codes": ["store_manager"],
        "scope_defs": [{"scope_type": "STORE", "store_code": "jiangnan"}],
    },
    {
        "username": "college.shiftlead",
        "full_name": "沈子昂",
        "nickname": "大学城值班",
        "mobile": "13900001004",
        "employee_no": "C001",
        "position_name": "值班经理",
        "store_code": "college",
        "org_key": "hall",
        "role_codes": ["shift_leader"],
        "scope_defs": [{"scope_type": "STORE", "store_code": "college"}],
    },
    {
        "username": "xinghe.bartender",
        "full_name": "程野",
        "nickname": "阿野",
        "mobile": "13900001005",
        "employee_no": "X002",
        "position_name": "调酒师",
        "store_code": "xinghe",
        "org_key": "bar",
        "role_codes": ["bartender"],
        "scope_defs": [{"scope_type": "SELF"}],
    },
    {
        "username": "xinghe.server",
        "full_name": "吴可欣",
        "nickname": "欣欣",
        "mobile": "13900001006",
        "employee_no": "X003",
        "position_name": "服务员",
        "store_code": "xinghe",
        "org_key": "hall",
        "role_codes": ["server"],
        "scope_defs": [{"scope_type": "SELF"}],
    },
    {
        "username": "jiangnan.bartender",
        "full_name": "赵子辰",
        "nickname": "小赵",
        "mobile": "13900001007",
        "employee_no": "J002",
        "position_name": "调酒师",
        "store_code": "jiangnan",
        "org_key": "bar",
        "role_codes": ["bartender"],
        "scope_defs": [{"scope_type": "SELF"}],
    },
    {
        "username": "multi.store.demo",
        "full_name": "陈亦凡",
        "nickname": "跨店示例",
        "mobile": "13900001008",
        "employee_no": "M001",
        "position_name": "星河店值班",
        "store_code": "xinghe",
        "org_key": "hall",
        "role_codes": ["shift_leader"],
        "store_role_codes": {
            "xinghe": ["shift_leader"],
            "jiangnan": ["server"],
        },
        "scope_defs": [
            {"scope_type": "STORE", "store_code": "xinghe"},
            {"scope_type": "STORE", "store_code": "jiangnan"},
        ],
        "extra_bindings": [
            {"store_code": "jiangnan", "org_key": "hall", "position_name": "江南店支援"}
        ],
    },
]


def _ensure_role(
    *, session: Session, code: str, name: str, permission_codes: list[str]
) -> Role:
    role = session.exec(select(Role).where(Role.code == code)).first()
    if not role:
        admin_user = session.exec(
            select(User).where(User.email == settings.FIRST_SUPERUSER)
        ).first()
        role = Role(
            code=code,
            name=name,
            status="ACTIVE",
            created_by_user_id=admin_user.id if admin_user else None,
        )
        session.add(role)
        session.commit()
        session.refresh(role)
    else:
        role.name = name
        role.status = "ACTIVE"
        session.add(role)
        session.commit()
        session.refresh(role)

    permissions = session.exec(
        select(Permission).where(Permission.code.in_(permission_codes))
    ).all()
    permission_ids = {item.id for item in permissions}
    existing_bindings = session.exec(
        select(RolePermission).where(RolePermission.role_id == role.id)
    ).all()
    existing_permission_ids = {item.permission_id for item in existing_bindings}

    for binding in existing_bindings:
        if binding.permission_id not in permission_ids:
            session.delete(binding)
    for permission in permissions:
        if permission.id not in existing_permission_ids:
            session.add(RolePermission(role_id=role.id, permission_id=permission.id))
    session.commit()
    ensure_self_role_grant(session=session, role_id=role.id)
    session.refresh(role)
    return role


def _ensure_role_grants(
    *,
    session: Session,
    role_code: str,
    grant_role_codes: list[str],
) -> None:
    role = session.exec(select(Role).where(Role.code == role_code)).first()
    if not role:
        return
    target_roles = session.exec(select(Role).where(Role.code.in_(grant_role_codes))).all()
    target_role_ids = {item.id for item in target_roles}
    existing = session.exec(
        select(RoleGrant).where(RoleGrant.grantor_role_id == role.id)
    ).all()
    existing_target_ids = {item.grantee_role_id for item in existing}
    for item in existing:
        if item.grantee_role_id not in target_role_ids:
            session.delete(item)
    for target_role in target_roles:
        if target_role.id not in existing_target_ids:
            session.add(RoleGrant(grantor_role_id=role.id, grantee_role_id=target_role.id))
    session.commit()


def _ensure_store(*, session: Session, code: str, name: str) -> Store:
    store = get_store_by_code(session=session, code=code)
    if not store:
        store = create_store(
            session=session,
            body=StoreCreate(code=code, name=name, status="ACTIVE"),
        )
    else:
        store.name = name
        store.status = "ACTIVE"
        store.updated_at = get_datetime_utc()
        session.add(store)
        session.commit()
        session.refresh(store)
    return store


def _get_org_node(
    *,
    session: Session,
    store_id,
    name: str,
    parent_id,
) -> OrgNode | None:
    statement = select(OrgNode).where(OrgNode.store_id == store_id).where(OrgNode.name == name)
    if parent_id is None:
        statement = statement.where(OrgNode.parent_id.is_(None))
    else:
        statement = statement.where(OrgNode.parent_id == parent_id)
    return session.exec(statement).first()


def _ensure_org_node(
    *,
    session: Session,
    store: Store,
    name: str,
    node_type: str,
    parent: OrgNode | None,
    sort_order: int,
) -> OrgNode:
    node = _get_org_node(
        session=session,
        store_id=store.id,
        name=name,
        parent_id=parent.id if parent else None,
    )
    if not node:
        node = create_org_node(
            session=session,
            body=OrgNodeCreate(
                store_id=store.id,
                parent_id=parent.id if parent else None,
                name=name,
                node_type=node_type,
                sort_order=sort_order,
                is_active=True,
            ),
            parent=parent,
        )
    else:
        node.node_type = node_type
        node.sort_order = sort_order
        node.is_active = True
        node.updated_at = get_datetime_utc()
        session.add(node)
        session.commit()
        session.refresh(node)
    return node


def _ensure_employee_user(
    *,
    session: Session,
    username: str,
    full_name: str,
    nickname: str,
    mobile: str,
) -> User:
    user = crud.get_user_by_username(session=session, username=username)
    if not user:
        user = crud.create_user(
            session=session,
            user_create=UserCreate(
                username=username,
                email=None,
                password=SAMPLE_USER_PASSWORD,
                user_type="EMPLOYEE",
                is_active=True,
                is_superuser=False,
                full_name=full_name,
                nickname=nickname,
                mobile=mobile,
                status="ACTIVE",
                primary_store_id=None,
                primary_department_id=None,
            ),
        )
    else:
        user.username = username
        user.full_name = full_name
        user.nickname = nickname
        user.mobile = mobile
        user.user_type = "EMPLOYEE"
        user.is_active = True
        user.status = "ACTIVE"
        user.updated_at = get_datetime_utc()
        session.add(user)
        session.commit()
        session.refresh(user)
        ensure_employee_profile(session=session, user=user)
    return user


def _ensure_employee_profile_seed(
    *,
    session: Session,
    user: User,
    employee_no: str,
    hired_at: datetime,
) -> EmployeeProfile:
    profile = get_employee_profile_by_user_id(session=session, user_id=user.id)
    if not profile:
        ensure_employee_profile(session=session, user=user)
        profile = get_employee_profile_by_user_id(session=session, user_id=user.id)
    assert profile is not None
    profile = update_employee_profile(
        session=session,
        profile=profile,
        employee_no=employee_no,
        hired_at=hired_at,
    )
    profile.employment_status = "ACTIVE"
    profile.left_at = None
    profile.updated_at = get_datetime_utc()
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


def _ensure_primary_binding(
    *,
    session: Session,
    user: User,
    org_node: OrgNode,
    position_name: str,
) -> UserOrgBinding:
    existing_binding = session.exec(
        select(UserOrgBinding)
        .where(UserOrgBinding.user_id == user.id)
        .where(UserOrgBinding.org_node_id == org_node.id)
    ).first()
    clear_primary_binding(session=session, user_id=user.id)
    sync_user_primary_org(session=session, user=user, org_node=org_node)
    if not existing_binding:
        existing_binding = UserOrgBinding(
            user_id=user.id,
            org_node_id=org_node.id,
            is_primary=True,
            position_name=position_name,
        )
    else:
        existing_binding.is_primary = True
        existing_binding.position_name = position_name
    session.add(existing_binding)
    session.commit()
    session.refresh(existing_binding)
    return existing_binding


def _ensure_extra_binding(
    *,
    session: Session,
    user: User,
    org_node: OrgNode,
    position_name: str,
) -> UserOrgBinding:
    binding = session.exec(
        select(UserOrgBinding)
        .where(UserOrgBinding.user_id == user.id)
        .where(UserOrgBinding.org_node_id == org_node.id)
    ).first()
    if not binding:
        binding = UserOrgBinding(
            user_id=user.id,
            org_node_id=org_node.id,
            is_primary=False,
            position_name=position_name,
        )
    else:
        binding.is_primary = False
        binding.position_name = position_name
    session.add(binding)
    session.commit()
    session.refresh(binding)
    return binding


def _ensure_employee_roles(
    *, session: Session, user: User, store_id, role_codes: list[str]
) -> None:
    roles = session.exec(select(Role).where(Role.code.in_(role_codes))).all()
    role_ids = {item.id for item in roles}
    existing = session.exec(
        select(UserStoreRole)
        .where(UserStoreRole.user_id == user.id)
        .where(UserStoreRole.store_id == store_id)
    ).all()
    existing_role_ids = {item.role_id for item in existing}
    for binding in existing:
        if binding.role_id not in role_ids:
            session.delete(binding)
    for role in roles:
        if role.id not in existing_role_ids:
            session.add(UserStoreRole(user_id=user.id, store_id=store_id, role_id=role.id))
    session.commit()


def _ensure_employee_store_roles(
    *,
    session: Session,
    user: User,
    store_map: dict[str, Store],
    primary_store_id,
    role_codes: list[str],
    store_role_codes: dict[str, list[str]] | None = None,
) -> None:
    if store_role_codes:
        for store_code, codes in store_role_codes.items():
            store = store_map.get(store_code)
            if not store:
                continue
            _ensure_employee_roles(
                session=session,
                user=user,
                store_id=store.id,
                role_codes=codes,
            )
        return
    _ensure_employee_roles(
        session=session,
        user=user,
        store_id=primary_store_id,
        role_codes=role_codes,
    )


def _ensure_employee_scopes(
    *,
    session: Session,
    user: User,
    scope_defs: list[dict],
    store_map: dict[str, Store],
    org_map: dict[tuple[str, str], OrgNode],
) -> None:
    existing = session.exec(select(UserDataScope).where(UserDataScope.user_id == user.id)).all()
    target_keys: set[tuple[str, str | None, str | None]] = set()
    for item in existing:
        session.delete(item)
    session.flush()
    for scope_def in scope_defs:
        scope_type = scope_def["scope_type"]
        store = store_map.get(scope_def.get("store_code")) if scope_def.get("store_code") else None
        org_node = (
            org_map.get((scope_def["store_code"], scope_def["org_key"]))
            if scope_def.get("org_key")
            else None
        )
        key = (scope_type, str(store.id) if store else None, str(org_node.id) if org_node else None)
        if key in target_keys:
            continue
        target_keys.add(key)
        session.add(
            UserDataScope(
                user_id=user.id,
                scope_type=scope_type,
                store_id=store.id if store else None,
                org_node_id=org_node.id if org_node else None,
            )
        )
    session.commit()


def _ensure_active_employment_record(
    *,
    session: Session,
    user: User,
    profile: EmployeeProfile,
    org_node: OrgNode,
    position_name: str,
) -> None:
    record = get_active_employment_record_by_user_id(session=session, user_id=user.id)
    if not record:
        create_employment_record(
            session=session,
            user_id=user.id,
            employee_no=profile.employee_no,
            hired_at=profile.hired_at,
            store_id=org_node.store_id,
            org_node_id=org_node.id,
            position_name=position_name,
        )
        return
    record.employee_no = profile.employee_no
    record.hired_at = profile.hired_at
    record.store_id = org_node.store_id
    record.org_node_id = org_node.id
    record.position_name = position_name
    record.employment_status = "ACTIVE"
    record.left_at = None
    record.leave_reason = None
    record.updated_at = get_datetime_utc()
    session.add(record)
    session.commit()


def seed_sample_data(session: Session) -> None:
    permission_map = {
        item.code: item for item in session.exec(select(Permission)).all()
    }
    missing_permissions = {
        code
        for role_def in SAMPLE_ROLE_DEFS
        for code in role_def["permission_codes"]
        if code not in permission_map
    }
    if missing_permissions:
        raise ValueError(f"缺少初始化权限定义：{', '.join(sorted(missing_permissions))}")

    for role_def in SAMPLE_ROLE_DEFS:
        _ensure_role(
            session=session,
            code=role_def["code"],
            name=role_def["name"],
            permission_codes=role_def["permission_codes"],
        )
    for role_code, grant_role_codes in SAMPLE_ROLE_GRANT_DEFS.items():
        _ensure_role_grants(
            session=session,
            role_code=role_code,
            grant_role_codes=grant_role_codes,
        )

    store_map: dict[str, Store] = {}
    org_map: dict[tuple[str, str], OrgNode] = {}
    for store_def in SAMPLE_STORE_DEFS:
        store = _ensure_store(
            session=session,
            code=store_def["code"],
            name=store_def["name"],
        )
        store_map[store_def["code"]] = store
        created_nodes: dict[str, OrgNode] = {}
        for sort_order, node_def in enumerate(store_def["org_nodes"], start=1):
            parent = created_nodes.get(node_def["parent"]) if node_def["parent"] else None
            node = _ensure_org_node(
                session=session,
                store=store,
                name=node_def["name"],
                node_type=node_def["node_type"],
                parent=parent,
                sort_order=sort_order,
            )
            created_nodes[node_def["key"]] = node
            org_map[(store_def["code"], node_def["key"])] = node

    base_hired_at = datetime(2025, 1, 1, 12, 0, 0)
    for index, employee_def in enumerate(SAMPLE_EMPLOYEE_DEFS, start=1):
        user = _ensure_employee_user(
            session=session,
            username=employee_def["username"],
            full_name=employee_def["full_name"],
            nickname=employee_def["nickname"],
            mobile=employee_def["mobile"],
        )
        profile = _ensure_employee_profile_seed(
            session=session,
            user=user,
            employee_no=employee_def["employee_no"],
            hired_at=base_hired_at.replace(day=min(index, 28)),
        )
        primary_org = org_map[(employee_def["store_code"], employee_def["org_key"])]
        _ensure_primary_binding(
            session=session,
            user=user,
            org_node=primary_org,
            position_name=employee_def["position_name"],
        )
        for extra_binding in employee_def.get("extra_bindings", []):
            extra_org = org_map[(extra_binding["store_code"], extra_binding["org_key"])]
            _ensure_extra_binding(
                session=session,
                user=user,
                org_node=extra_org,
                position_name=extra_binding["position_name"],
            )
        _ensure_employee_store_roles(
            session=session,
            user=user,
            store_map=store_map,
            primary_store_id=primary_org.store_id,
            role_codes=employee_def["role_codes"],
            store_role_codes=employee_def.get("store_role_codes"),
        )
        _ensure_employee_scopes(
            session=session,
            user=user,
            scope_defs=employee_def["scope_defs"],
            store_map=store_map,
            org_map=org_map,
        )
        _ensure_active_employment_record(
            session=session,
            user=user,
            profile=profile,
            org_node=primary_org,
            position_name=employee_def["position_name"],
        )


def init_db(session: Session) -> None:
    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            username=settings.FIRST_SUPERUSER,
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)
    else:
        user.username = settings.FIRST_SUPERUSER
        user.email = settings.FIRST_SUPERUSER
        user.hashed_password = get_password_hash(settings.FIRST_SUPERUSER_PASSWORD)
        user.is_superuser = True
        user.is_active = True
        user.status = "ACTIVE"
        session.add(user)
        session.commit()
        session.refresh(user)
        ensure_employee_profile(session=session, user=user)

    role = session.exec(select(Role).where(Role.code == ADMIN_ROLE_CODE)).first()
    if not role:
        role = Role(
            code=ADMIN_ROLE_CODE,
            name="系统管理员",
            created_by_user_id=user.id,
        )
        session.add(role)
        session.commit()
        session.refresh(role)
    elif role.created_by_user_id is None:
        role.created_by_user_id = user.id
        session.add(role)
        session.commit()
        session.refresh(role)
    ensure_self_role_grant(session=session, role_id=role.id)

    seed_permissions(session=session, permission_defs=DEFAULT_PERMISSION_DEFS)
    permission_ids = [item.id for item in session.exec(select(Permission)).all()]
    existing_permission_ids = {
        item.permission_id
        for item in session.exec(
            select(RolePermission).where(RolePermission.role_id == role.id)
        ).all()
    }
    for permission_id in permission_ids:
        if permission_id not in existing_permission_ids:
            session.add(RolePermission(role_id=role.id, permission_id=permission_id))

    all_scope = session.exec(
        select(UserDataScope)
        .where(UserDataScope.user_id == user.id)
        .where(UserDataScope.scope_type == "ALL")
    ).first()
    if not all_scope:
        session.add(UserDataScope(user_id=user.id, scope_type="ALL"))
    session.commit()

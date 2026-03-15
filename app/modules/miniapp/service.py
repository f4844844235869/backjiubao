import uuid

from sqlmodel import Session, select

from app.models import User
from app.modules.employee.service import get_employee_profile_by_user_id
from app.modules.miniapp.models import (
    MiniappAccount,
    MiniappLinkedEmployeePublic,
    MiniappPhoneRelationPublic,
    UserPhoneBinding,
)


def get_miniapp_account_by_openid(
    *, session: Session, app_id: str, openid: str
) -> MiniappAccount | None:
    statement = select(MiniappAccount).where(
        MiniappAccount.app_id == app_id,
        MiniappAccount.openid == openid,
    )
    return session.exec(statement).first()


def get_latest_verified_phone_binding_by_user_id(
    *, session: Session, user_id: uuid.UUID
) -> UserPhoneBinding | None:
    statement = (
        select(UserPhoneBinding)
        .where(
            UserPhoneBinding.user_id == user_id,
            UserPhoneBinding.is_verified.is_(True),
        )
        .order_by(UserPhoneBinding.verified_at.desc(), UserPhoneBinding.created_at.desc())
    )
    return session.exec(statement).first()


def build_miniapp_phone_relation(
    *, session: Session, user: User, current_store_id: uuid.UUID | None = None
) -> MiniappPhoneRelationPublic:
    binding = get_latest_verified_phone_binding_by_user_id(session=session, user_id=user.id)
    if not binding:
        return MiniappPhoneRelationPublic(current_store_id=current_store_id)

    statement = (
        select(User)
        .where(
            User.user_type == "EMPLOYEE",
            User.mobile == binding.phone,
        )
        .order_by(User.created_at.desc())
    )
    if current_store_id:
        statement = statement.where(User.primary_store_id == current_store_id)
    employee_users = session.exec(statement).all()
    related_employees: list[MiniappLinkedEmployeePublic] = []
    for employee_user in employee_users:
        profile = get_employee_profile_by_user_id(session=session, user_id=employee_user.id)
        related_employees.append(
            MiniappLinkedEmployeePublic(
                user_id=employee_user.id,
                username=employee_user.username,
                full_name=employee_user.full_name,
                nickname=employee_user.nickname,
                mobile=employee_user.mobile,
                is_active=employee_user.is_active,
                status=employee_user.status,
                primary_store_id=employee_user.primary_store_id,
                primary_department_id=employee_user.primary_department_id,
                employee_no=profile.employee_no if profile else None,
                employment_status=profile.employment_status if profile else None,
            )
        )
    return MiniappPhoneRelationPublic(
        current_store_id=current_store_id,
        phone=binding.phone,
        country_code=binding.country_code,
        related_employees=related_employees,
    )

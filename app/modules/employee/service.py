import uuid

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models import User
from app.models.base import get_datetime_utc
from app.modules.employee.models import EmployeeEmploymentRecord, EmployeeProfile
from app.modules.org.models import OrgNode
from app.modules.org.service import build_org_prefix_chain


def get_employee_profile_by_user_id(
    *, session: Session, user_id: uuid.UUID
) -> EmployeeProfile | None:
    statement = select(EmployeeProfile).where(EmployeeProfile.user_id == user_id)
    return session.exec(statement).first()


def list_employment_records_by_user_id(
    *, session: Session, user_id: uuid.UUID
) -> list[EmployeeEmploymentRecord]:
    statement = (
        select(EmployeeEmploymentRecord)
        .where(EmployeeEmploymentRecord.user_id == user_id)
        .order_by(EmployeeEmploymentRecord.hired_at.desc(), EmployeeEmploymentRecord.created_at.desc())
    )
    return list(session.exec(statement).all())


def get_active_employment_record_by_user_id(
    *, session: Session, user_id: uuid.UUID
) -> EmployeeEmploymentRecord | None:
    statement = (
        select(EmployeeEmploymentRecord)
        .where(EmployeeEmploymentRecord.user_id == user_id)
        .where(EmployeeEmploymentRecord.employment_status == "ACTIVE")
        .order_by(EmployeeEmploymentRecord.hired_at.desc(), EmployeeEmploymentRecord.created_at.desc())
    )
    return session.exec(statement).first()


def ensure_employee_profile(*, session: Session, user: User) -> EmployeeProfile | None:
    return _ensure_employee_profile(session=session, user=user, auto_commit=True)


def _ensure_employee_profile(
    *, session: Session, user: User, auto_commit: bool
) -> EmployeeProfile | None:
    if user.user_type != "EMPLOYEE":
        return None
    profile = get_employee_profile_by_user_id(session=session, user_id=user.id)
    if profile:
        return profile
    profile = EmployeeProfile(
        user_id=user.id,
        employment_status="ACTIVE",
        hired_at=get_datetime_utc(),
    )
    session.add(profile)
    try:
        if auto_commit:
            session.commit()
            session.refresh(profile)
        else:
            session.flush()
    except IntegrityError:
        session.rollback()
        return get_employee_profile_by_user_id(session=session, user_id=user.id)
    return profile


def generate_employee_no(
    *,
    session: Session,
    org_node: OrgNode,
) -> str:
    prefix = build_org_prefix_chain(session=session, node=org_node)

    existing_nos = session.exec(
        select(EmployeeProfile.employee_no).where(
            EmployeeProfile.employee_no.is_not(None),
            EmployeeProfile.employee_no.startswith(prefix),
        )
    ).all()
    max_sequence = 0
    for item in existing_nos:
        if not item:
            continue
        suffix = item.removeprefix(prefix)
        if len(suffix) == 4 and suffix.isdigit():
            max_sequence = max(max_sequence, int(suffix))

    return f"{prefix}{max_sequence + 1:04d}"


def update_employee_profile(
    *,
    session: Session,
    profile: EmployeeProfile,
    employee_no: str | None = None,
    hired_at=None,
) -> EmployeeProfile:
    if employee_no is not None:
        profile.employee_no = employee_no
    if hired_at is not None:
        profile.hired_at = hired_at
    profile.updated_at = get_datetime_utc()
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


def create_employment_record(
    *,
    session: Session,
    user_id: uuid.UUID,
    employee_no: str | None,
    hired_at,
    store_id: uuid.UUID | None,
    org_node_id: uuid.UUID | None,
    position_name: str | None,
) -> EmployeeEmploymentRecord:
    record = EmployeeEmploymentRecord(
        user_id=user_id,
        employee_no=employee_no,
        employment_status="ACTIVE",
        hired_at=hired_at or get_datetime_utc(),
        store_id=store_id,
        org_node_id=org_node_id,
        position_name=position_name,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def mark_employee_left(
    *,
    session: Session,
    user: User,
    profile: EmployeeProfile,
    left_at,
    leave_reason: str | None,
) -> EmployeeProfile:
    actual_left_at = left_at or get_datetime_utc()
    profile.employment_status = "LEFT"
    profile.left_at = actual_left_at
    profile.updated_at = get_datetime_utc()
    user.is_active = False
    user.status = "LEFT"
    user.updated_at = get_datetime_utc()
    session.add(profile)
    session.add(user)

    record = get_active_employment_record_by_user_id(session=session, user_id=user.id)
    if record:
        record.employment_status = "LEFT"
        record.left_at = actual_left_at
        record.leave_reason = leave_reason
        record.updated_at = get_datetime_utc()
        session.add(record)

    session.commit()
    session.refresh(profile)
    return profile


def update_active_employment_record_assignment(
    *,
    session: Session,
    user_id: uuid.UUID,
    org_node_id: uuid.UUID | None = None,
    position_name: str | None = None,
) -> EmployeeEmploymentRecord | None:
    record = get_active_employment_record_by_user_id(session=session, user_id=user_id)
    if not record:
        return None
    if org_node_id is not None:
        record.org_node_id = org_node_id
    if position_name is not None:
        record.position_name = position_name
    record.updated_at = get_datetime_utc()
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

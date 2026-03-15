from fastapi.encoders import jsonable_encoder
from pwdlib.hashers.bcrypt import BcryptHasher
from sqlmodel import Session

from app import crud
from app.core.security import verify_password
from app.models import User, UserCreate, UserUpdate
from tests.utils.utils import random_email, random_lower_string


def build_user_create() -> UserCreate:
    return UserCreate(
        username=random_lower_string(),
        email=random_email(),
        password="password1234",
    )


def test_create_user(db: Session) -> None:
    user_in = build_user_create()
    user = crud.create_user(session=db, user_create=user_in)
    assert user.email == user_in.email
    assert user.username == user_in.username
    assert hasattr(user, "hashed_password")


def test_authenticate_user_by_email(db: Session) -> None:
    user_in = build_user_create()
    user = crud.create_user(session=db, user_create=user_in)
    authenticated_user = crud.authenticate(
        session=db, account=user.email, password=user_in.password
    )
    assert authenticated_user
    assert user.email == authenticated_user.email


def test_authenticate_user_by_username(db: Session) -> None:
    user_in = build_user_create()
    user = crud.create_user(session=db, user_create=user_in)
    authenticated_user = crud.authenticate(
        session=db, account=user.username, password=user_in.password
    )
    assert authenticated_user
    assert user.username == authenticated_user.username


def test_not_authenticate_user(db: Session) -> None:
    user = crud.authenticate(
        session=db, account=random_lower_string(), password=random_lower_string()
    )
    assert user is None


def test_check_user_flags(db: Session) -> None:
    user = crud.create_user(
        session=db,
        user_create=UserCreate(
            username=random_lower_string(),
            email=random_email(),
            password="password1234",
            is_active=False,
            is_superuser=True,
        ),
    )
    assert user.is_active is False
    assert user.is_superuser is True


def test_get_user(db: Session) -> None:
    user = crud.create_user(session=db, user_create=build_user_create())
    user_2 = db.get(User, user.id)
    assert user_2
    assert jsonable_encoder(user) == jsonable_encoder(user_2)


def test_update_user(db: Session) -> None:
    user = crud.create_user(session=db, user_create=build_user_create())
    new_password = "updated-password123"
    crud.update_user(
        session=db,
        db_user=user,
        user_in=UserUpdate(password=new_password, nickname="新昵称"),
    )
    user_2 = db.get(User, user.id)
    assert user_2
    assert user_2.nickname == "新昵称"
    verified, _ = verify_password(new_password, user_2.hashed_password)
    assert verified


def test_authenticate_user_with_bcrypt_upgrades_to_argon2(db: Session) -> None:
    email = random_email()
    username = random_lower_string()
    password = "password1234"

    bcrypt_hasher = BcryptHasher()
    bcrypt_hash = bcrypt_hasher.hash(password)

    user = User(username=username, email=email, hashed_password=bcrypt_hash)
    db.add(user)
    db.commit()
    db.refresh(user)

    authenticated_user = crud.authenticate(session=db, account=email, password=password)
    assert authenticated_user
    db.refresh(authenticated_user)
    assert authenticated_user.hashed_password.startswith("$argon2")

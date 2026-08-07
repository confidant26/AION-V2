from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse


class UserAlreadyExistsError(Exception):
    pass


class AuthenticationError(Exception):
    pass


class AuthService:
    def __init__(self, db: Session) -> None:
        self.repository = UserRepository(db)

    def register(self, request: UserRegisterRequest) -> UserResponse:
        if self.repository.get_by_email(request.email) is not None:
            raise UserAlreadyExistsError("A user with this email already exists.")
        try:
            user = self.repository.create(
                email=request.email,
                password_hash=hash_password(request.password),
                display_name=request.display_name,
            )
        except IntegrityError as exc:
            self.repository.db.rollback()
            raise UserAlreadyExistsError("A user with this email already exists.") from exc
        return UserResponse.model_validate(user)

    def login(self, request: UserLoginRequest) -> TokenResponse:
        user = self.repository.get_by_email(request.email)
        if user is None or not user.active or not verify_password(request.password, user.password_hash):
            raise AuthenticationError("Invalid email or password.")
        token, expires_at = create_access_token(user_id=user.id, email=user.email)
        return TokenResponse(access_token=token, expires_at=expires_at, user=UserResponse.model_validate(user))

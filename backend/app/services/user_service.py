from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UpdateProfile,
    ChangePassword,
    ForgotPassword,
    ResetPassword
)

import secrets
from datetime import datetime, timedelta, UTC

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token
)


class UserService:

    # ==========================
    # CREATE USER
    # ==========================
    @staticmethod
    async def create_user(user_data: UserCreate):

        existing_user = await User.find_one(
            User.email == user_data.email.lower()
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists."
            )

        user = User(
            name=user_data.name,
            email=user_data.email.lower(),
            hashed_password=hash_password(
                user_data.password
            ),
            role=user_data.role or "Operations Director",
            department=user_data.department
        )

        await user.insert()

        return user

    # ==========================
    # GET USER BY EMAIL
    # ==========================
    @staticmethod
    async def get_user_by_email(email: str):

        return await User.find_one(
            User.email == email.lower()
        )

    # ==========================
    # GET USER BY ID
    # ==========================
    @staticmethod
    async def get_user_by_id(user_id: str):

        return await User.get(user_id)

    # ==========================
    # LOGIN
    # ==========================
    @staticmethod
    async def authenticate_user(
        email: str,
        password: str
    ):

        user = await User.find_one(
            User.email == email.lower()
        )

        if user is None:

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )

        if not verify_password(
            password,
            user.hashed_password
        ):

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )

        access_token = create_access_token(
            subject=str(user.id)
        )

        return {
            "user": user,
            "access_token": access_token
        }

    # ==========================
    # UPDATE PROFILE
    # ==========================
    @staticmethod
    async def update_profile(
        current_user: User,
        profile: UpdateProfile
    ):

        current_user.name = profile.name

        await current_user.save()

        return current_user

    # ==========================
    # CHANGE PASSWORD
    # ==========================
    @staticmethod
    async def change_password(
        current_user: User,
        passwords: ChangePassword
    ):

        if not verify_password(
            passwords.old_password,
            current_user.hashed_password
        ):

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Old password is incorrect."
            )

        current_user.hashed_password = hash_password(
            passwords.new_password
        )

        await current_user.save()

        return True

    # ==========================
    # DELETE ACCOUNT
    # ==========================
    @staticmethod
    async def delete_account(
        current_user: User
    ):

        await current_user.delete()

        return True

    # ==========================
    # FORGOT PASSWORD
    # ==========================
    @staticmethod
    async def forgot_password(
        email_data: ForgotPassword
    ):
        user = await User.find_one(
            User.email == email_data.email.lower()
        )

        if not user:
            # Don't throw error to prevent email enumeration, just return True
            return True

        # Generate a secure reset token
        reset_token = secrets.token_urlsafe(32)
        user.reset_token = reset_token
        user.reset_token_expiry = datetime.now(UTC) + timedelta(hours=1)
        await user.save()

        # In a real app, send an email. For now, print to console.
        reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
        print(f"\n[{user.email}] Password reset link: {reset_link}\n")

        return True

    # ==========================
    # RESET PASSWORD
    # ==========================
    @staticmethod
    async def reset_password(
        reset_data: ResetPassword
    ):
        user = await User.find_one(
            User.reset_token == reset_data.token
        )

        if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token."
            )

        user.hashed_password = hash_password(
            reset_data.new_password
        )
        user.reset_token = None
        user.reset_token_expiry = None

        await user.save()

        return True
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UpdateProfile,
    ChangePassword,
    ForgotPassword,
    ResetPassword
)
from app.services.user_service import UserService

router = APIRouter()


# ==========================================================
# SIGNUP
# ==========================================================

@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def signup(user: UserCreate):

    created_user = await UserService.create_user(user)

    return UserResponse(
        id=str(created_user.id),
        name=created_user.name,
        email=created_user.email,
        role=created_user.role,
        department=created_user.department
    )


# ==========================================================
# LOGIN (JSON)
# Used by Frontend
# ==========================================================

@router.post(
    "/login",
    response_model=Token,
    summary="Login (JSON)",
)
async def login(user: UserLogin):

    result = await UserService.authenticate_user(
        email=user.email,
        password=user.password,
    )

    return Token(
        access_token=result["access_token"],
        token_type="bearer",
    )


# ==========================================================
# OAUTH2 LOGIN
# Used by Swagger Authorize
# ==========================================================

@router.post(
    "/token",
    response_model=Token,
    summary="OAuth2 Login",
)
async def oauth2_login(
    form_data: OAuth2PasswordRequestForm = Depends()
):

    result = await UserService.authenticate_user(
        email=form_data.username,
        password=form_data.password,
    )

    return Token(
        access_token=result["access_token"],
        token_type="bearer",
    )


# ==========================================================
# CURRENT USER
# ==========================================================

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current logged in user",
)
async def get_me(
    current_user: User = Depends(get_current_user),
):

    return UserResponse(
        id=str(current_user.id),
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        department=current_user.department
    )


# ==========================================================
# UPDATE PROFILE
# ==========================================================

@router.put(
    "/profile",
    response_model=UserResponse,
    summary="Update profile",
)
async def update_profile(
    profile: UpdateProfile,
    current_user: User = Depends(get_current_user),
):

    updated_user = await UserService.update_profile(
        current_user=current_user,
        profile=profile,
    )

    return UserResponse(
        id=str(updated_user.id),
        name=updated_user.name,
        email=updated_user.email,
        role=updated_user.role,
        department=updated_user.department
    )


# ==========================================================
# CHANGE PASSWORD
# ==========================================================

@router.put(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change password",
)
async def change_password(
    passwords: ChangePassword,
    current_user: User = Depends(get_current_user),
):

    await UserService.change_password(
        current_user=current_user,
        passwords=passwords,
    )

    return {
        "message": "Password changed successfully."
    }


# ==========================================================
# DELETE ACCOUNT
# ==========================================================

@router.delete(
    "/delete-account",
    status_code=status.HTTP_200_OK,
    summary="Delete account",
)
async def delete_account(
    current_user: User = Depends(get_current_user),
):

    await UserService.delete_account(current_user)

    return {
        "message": "Account deleted successfully."
    }

# ==========================================================
# FORGOT PASSWORD
# ==========================================================

@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Request a password reset link",
)
async def forgot_password(
    email_data: ForgotPassword
):
    await UserService.forgot_password(email_data)
    return {
        "message": "If that email is in our database, we will send a password reset link."
    }

# ==========================================================
# RESET PASSWORD
# ==========================================================

@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset password with token",
)
async def reset_password(
    reset_data: ResetPassword
):
    await UserService.reset_password(reset_data)
    return {
        "message": "Password reset successfully."
    }
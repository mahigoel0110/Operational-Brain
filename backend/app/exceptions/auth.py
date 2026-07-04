from fastapi import HTTPException, status


class AuthenticationError(HTTPException):

    def __init__(self):

        super().__init__(

            status_code=status.HTTP_401_UNAUTHORIZED,

            detail="Invalid email or password",

            headers={
                "WWW-Authenticate": "Bearer"
            }
        )


class UserAlreadyExistsError(HTTPException):

    def __init__(self):

        super().__init__(

            status_code=status.HTTP_409_CONFLICT,

            detail="Email already exists."
        )


class InvalidTokenError(HTTPException):

    def __init__(self):

        super().__init__(

            status_code=status.HTTP_401_UNAUTHORIZED,

            detail="Invalid token.",

            headers={
                "WWW-Authenticate": "Bearer"
            }
        )
from app.core.security import create_access_token, decode_access_token

token = create_access_token(
    {
        "sub": "mahi@gmail.com"
    }
)

print(token)

print()

print(decode_access_token(token))
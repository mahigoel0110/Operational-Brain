from app.core.security import (

    create_access_token,

    decode_access_token
)

token = create_access_token(

    "mahi@gmail.com"
)

print(

    decode_access_token(token)
)
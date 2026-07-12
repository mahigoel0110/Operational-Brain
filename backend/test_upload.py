import requests

url = "http://localhost:8000/documents/"
# Need to login first to get a token
login_data = {
    "username": "test@example.com",
    "password": "password"
}
# wait, there's no way to know if test@example.com exists.

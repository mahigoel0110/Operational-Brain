import os
import secrets
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from app.models.user import User
from app.core.security import create_access_token, hash_password

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

@router.get("/google/login", summary="Google OAuth Login")
async def google_login():
    """Redirects to Google OAuth authorization URL. Falls back to mock flow if no Client ID is provided."""
    if not GOOGLE_CLIENT_ID:
        # Mock mode
        return RedirectResponse(url="/api/oauth/google/callback?mock=true")
        
    redirect_uri = "http://localhost:8000/api/oauth/google/callback"
    url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={GOOGLE_CLIENT_ID}&redirect_uri={redirect_uri}&response_type=code&scope=openid email profile"
    return RedirectResponse(url=url)

@router.get("/google/callback", summary="Google OAuth Callback")
async def google_callback(request: Request, code: str = None, mock: str = None):
    """Handles OAuth callback, exchanges code for token, and redirects to frontend."""
    email = ""
    name = ""
    if mock == "true":
        email = "test.oauth@example.com"
        name = "Mock OAuth User"
    else:
        if not code:
            raise HTTPException(status_code=400, detail="Missing authorization code")
        # In a complete implementation, use httpx here to POST to https://oauth2.googleapis.com/token
        # and then GET https://www.googleapis.com/oauth2/v2/userinfo
        # For placeholder purposes:
        email = "placeholder.oauth@example.com"
        name = "Placeholder OAuth User"
        
    # Find or create user
    user = await User.find_one(User.email == email)
    if not user:
        user = User(
            name=name,
            email=email,
            hashed_password=hash_password(secrets.token_urlsafe(16)),
            is_verified=True
        )
        await user.insert()
        
    access_token = create_access_token(subject=str(user.id))
    
    # Render an intermediate page to save token to localStorage and redirect
    html_content = f"""
    <!DOCTYPE html>
    <html>
        <head>
            <title>Authenticating...</title>
        </head>
        <body style="background-color: #0a0a0a; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; font-family: sans-serif;">
            <div>Authenticating...</div>
            <script>
                // Save token and navigate to dashboard
                localStorage.setItem('token', '{access_token}');
                window.location.href = '{FRONTEND_URL}/dashboard';
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

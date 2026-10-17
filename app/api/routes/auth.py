from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth

from app.core.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    FRONTEND_URL,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# =====================================================
# GOOGLE OAUTH
# =====================================================

oauth = OAuth()


oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url=(
        "https://accounts.google.com/.well-known/openid-configuration"
    ),
    client_kwargs={
        "scope": "openid email profile"
    },
)


# =====================================================
# LOGIN
# =====================================================

@router.get("/login")
async def login(request: Request):

    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:

        raise HTTPException(
            status_code=503,
            detail=(
                "Google sign-in is not configured on this server. "
                "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
            ),
        )

    redirect_uri = GOOGLE_REDIRECT_URI

    return await oauth.google.authorize_redirect(
        request,
        redirect_uri
    )


# =====================================================
# CALLBACK
# =====================================================

@router.get("/callback")
async def callback(request: Request):

    token = await oauth.google.authorize_access_token(
        request
    )

    user = token.get("userinfo")

    if not user:
        return {
            "success": False,
            "message": "Unable to retrieve Google user information."
        }

    request.session["user"] = {
        "id": user.get("sub"),
        "name": user.get("name"),
        "email": user.get("email"),
        "picture": user.get("picture"),
    }

    return RedirectResponse(
        url=f"{FRONTEND_URL}/"
    )


# =====================================================
# CURRENT USER
# =====================================================

@router.get("/me")
async def get_current_user(request: Request):

    user = request.session.get("user")

    if not user:

        return {
            "authenticated": False,
            "user": None
        }

    return {
        "authenticated": True,
        "user": user
    }


# =====================================================
# LOGOUT
# =====================================================

@router.get("/logout")
async def logout(request: Request):

    request.session.clear()

    return RedirectResponse(
        url=f"{FRONTEND_URL}/"
    )
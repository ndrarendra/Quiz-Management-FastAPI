# app/routers/ui_login.py
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.models.user import User as UserModel
from app.utils import verify_password
from app.config import templates  # now we import from config
from app.auth import create_access_token, get_db

router = APIRouter(prefix="/ui", tags=["UI"])

@router.get("/login", response_class=HTMLResponse, tags=["UI"])
def ui_login_page(request: Request):
    """
    Render the login page.

    This endpoint displays the login form to the user.

    Parameters:
        request (Request): The incoming HTTP request.

    Returns:
        TemplateResponse: Renders the "login.html" template with the request context.
    """
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse, tags=["UI"])
async def ui_login(
    request: Request,
    db: Session = Depends(get_db),
    username: str = Form(...),
    password: str = Form(...)
):
    """
    Process user login.

    This endpoint authenticates the user by checking the provided username and password.
    If the credentials are valid, an access token is created and set as an HTTP-only cookie.
    The user is then redirected to either the admin or user dashboard based on their privileges.

    Parameters:
        request (Request): The incoming HTTP request.
        db (Session): Database session dependency.
        username (str): The username submitted from the login form.
        password (str): The password submitted from the login form.

    Returns:
        TemplateResponse: Renders the login page with an error message if authentication fails.
        RedirectResponse: Redirects the user to the appropriate dashboard on successful login.
    """
    # Query the database for a user matching the submitted username.
    db_user = db.query(UserModel).filter(UserModel.username == username).first()
    
    # Verify that the user exists and the password is correct.
    if not db_user or not verify_password(password, db_user.hashed_password):
        # If authentication fails, re-render the login page with an error message.
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "Invalid username or password"
        })
    
    # Create an access token with the user's username in the payload.
    token = create_access_token(data={"sub": db_user.username})
    
    # Determine the redirect URL based on the user's admin status.
    if db_user.is_admin:
        redirect_url = "/ui/admin"
    else:
        redirect_url = "/ui/user"
    
    # Create a redirect response to the determined URL.
    response = RedirectResponse(url=redirect_url, status_code=302)
    
    # Set the access token as an HTTP-only cookie for security.
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response


@router.get("/logout", response_class=HTMLResponse, tags=["UI"])
def ui_logout(request: Request):
    """
    Log out the user.

    This endpoint clears the access token cookie and redirects the user to the login page.

    Parameters:
        request (Request): The incoming HTTP request.

    Returns:
        RedirectResponse: Redirects the user to the login page.
    """
    response = RedirectResponse(url="/ui/login", status_code=302)
    # Delete the "access_token" cookie to log the user out.
    response.delete_cookie("access_token")
    return response

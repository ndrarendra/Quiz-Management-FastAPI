# app/routers/admin_users.py
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.models.user import User as UserModel
from app.utils import hash_password
from app.config import templates  # now we import from config
from app.auth import get_current_user_from_cookie,get_db

router = APIRouter(prefix="/ui/admin/users", tags=["UI", "Admin"])

@router.get("/", response_class=HTMLResponse, tags=["UI", "Admin"])
def admin_user_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user_from_cookie)
):
    """
    Display a list of all users in the system (Admin only).

    This endpoint retrieves all user records from the database and renders them in an HTML template.
    It first validates that the current user has admin privileges.

    Parameters:
        request (Request): The incoming HTTP request.
        db (Session): The database session dependency.
        current_user (UserModel): The currently logged-in user retrieved from a cookie.

    Returns:
        A TemplateResponse rendering the list of users.
    """
    # Ensure that the current user is an admin.
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    # Retrieve all users from the database.
    users = db.query(UserModel).all()
    
    # Render the template with the list of users.
    return templates.TemplateResponse("/admin/users/list.html", {
        "request": request,
        "users": users,
        "user": current_user
    })


@router.get("/create", response_class=HTMLResponse, tags=["UI", "Admin"])
def admin_create_user_get(
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user_from_cookie)
):
    """
    Render the form to create a new user (Admin only).

    This endpoint renders an HTML form that allows an admin to create a new user.

    Parameters:
        request (Request): The incoming HTTP request.
        db (Session): The database session dependency.
        current_user (UserModel): The currently logged-in user.

    Returns:
        A TemplateResponse rendering the user creation form.
    """
    # Ensure that the current user is an admin.
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    # Render the create user form.
    return templates.TemplateResponse("/admin/users/create.html", {
        "request": request,
        "user": current_user
    })


@router.post("/create", response_class=HTMLResponse, tags=["UI", "Admin"])
def admin_create_user_post(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    is_admin: Optional[bool] = Form(False),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user_from_cookie)
):
    """
    Process the user creation form submission.

    This endpoint creates a new user in the system after validating that the username or email
    are not already registered. It then hashes the provided password and stores the new user record.

    Parameters:
        request (Request): The incoming HTTP request.
        username (str): The desired username from the form.
        email (str): The email address from the form.
        password (str): The raw password from the form.
        is_admin (bool, optional): Boolean flag indicating if the new user should have admin rights.
        db (Session): The database session dependency.
        current_user (UserModel): The currently logged-in user.

    Returns:
        A RedirectResponse to the admin user list if successful or a TemplateResponse with an error.
    """
    # Ensure that the current user is an admin.
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")

    # Check if a user with the same username or email already exists.
    existing = db.query(UserModel).filter(
        (UserModel.username == username) | (UserModel.email == email)
    ).first()
    if existing:
        # Return the create form with an error message if a duplicate is found.
        return templates.TemplateResponse("/admin/users/create.html", {
            "request": request,
            "error": "Username or email already registered",
            "user": current_user
        })

    # Create a new user instance.
    new_user = UserModel(
        username=username,
        email=email,
        hashed_password=hash_password(password),  # Hash the password before storing it.
        is_admin=is_admin
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Redirect to the user list after successful creation.
    return RedirectResponse(url="/ui/admin/users", status_code=302)


@router.get("/{user_id}/delete", response_class=HTMLResponse, tags=["UI", "Admin"])
def admin_delete_user_get(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user_from_cookie)
):
    """
    Render a confirmation page to delete a user.

    This endpoint displays a confirmation page for deleting a user. It verifies that the user exists
    and that the current user has admin privileges.

    Parameters:
        user_id (int): The unique identifier of the user to delete.
        request (Request): The incoming HTTP request.
        db (Session): The database session dependency.
        current_user (UserModel): The currently logged-in user.

    Returns:
        A TemplateResponse rendering the delete confirmation page, or an HTMLResponse with an error message if the user is not found.
    """
    # Ensure that the current user is an admin.
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")

    # Retrieve the user to delete from the database.
    user_to_delete = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user_to_delete:
        return HTMLResponse("<h2>User not found</h2>", status_code=404)
    
    # Render the confirmation page.
    return templates.TemplateResponse("/admin/users/delete.html", {
        "request": request,
        "user_obj": user_to_delete,
        "user": current_user
    })


@router.post("/{user_id}/delete", response_class=HTMLResponse, tags=["UI", "Admin"])
def admin_delete_user_post(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user_from_cookie)
):
    """
    Delete a user after confirmation.

    This endpoint processes the deletion of a user after the admin confirms the action. It verifies
    that the user exists and then removes the user from the database.

    Parameters:
        user_id (int): The unique identifier of the user to be deleted.
        request (Request): The incoming HTTP request.
        db (Session): The database session dependency.
        current_user (UserModel): The currently logged-in user.

    Returns:
        A RedirectResponse to the admin user list page after deletion.
    """
    # Ensure that the current user is an admin.
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")

    # Retrieve the user to be deleted.
    user_to_delete = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user_to_delete:
        return HTMLResponse("<h2>User not found</h2>", status_code=404)

    # Delete the user and commit the transaction.
    db.delete(user_to_delete)
    db.commit()

    # Redirect to the user list page.
    return RedirectResponse(url="/ui/admin/users", status_code=302)

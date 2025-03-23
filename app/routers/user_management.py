# app/routers/user_management.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.user import User as UserModel
from app.schemas.user import UserCreate, UserOut, Token
from app.utils import hash_password, verify_password
from app.auth import get_db,create_access_token, get_current_user_token
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_cache.decorator import cache

router = APIRouter(prefix="/users", tags=["User Management"])

@router.post("/register", response_model=UserOut, tags=["User Management"])
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.

    This endpoint registers a new user by first verifying that the username or email does not
    already exist in the database. If the user is unique, the password is hashed and a new user record
    is created.

    Parameters:
        user (UserCreate): The user registration data containing username, email, and password.
        db (Session): Database session dependency.

    Returns:
        UserOut: The newly created user data in the output schema format.
    """
    # Check if a user with the same username or email already exists.
    existing_user = db.query(UserModel).filter(
        (UserModel.username == user.username) | (UserModel.email == user.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    # Create a new user instance with a hashed password.
    new_user = UserModel(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Return the newly created user.
    return new_user


@router.post("/login", response_model=Token, tags=["User Management"])
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate and login a user.

    This endpoint validates user credentials (username and password) using the OAuth2 password flow.
    Upon successful authentication, a JWT access token is created and returned.

    Parameters:
        form_data (OAuth2PasswordRequestForm): Contains the username and password from the login form.
        db (Session): Database session dependency.

    Returns:
        dict: A dictionary containing the access token and token type ("bearer").
    """
    # Retrieve the user based on the provided username.
    db_user = db.query(UserModel).filter(UserModel.username == form_data.username).first()
    
    # Validate the user and check that the password matches.
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # Create a JWT access token with the user's username as the subject.
    access_token = create_access_token(data={"sub": db_user.username})
    
    # Return the token in the expected format.
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut, tags=["User Management"])
@cache(expire=60)  # Cache for 60 seconds to improve performance.
def read_users_me(current_user: UserModel = Depends(get_current_user_token)):
    """
    Retrieve the current authenticated user's information.

    This endpoint uses the token-based dependency to fetch and return the current user's details.

    Parameters:
        current_user (UserModel): The user data obtained from the token dependency.

    Returns:
        UserOut: The current user's information in the output schema format.
    """
    return current_user


@router.get("/admin/users", response_model=list[UserOut], tags=["User Management", "Admin"])
@cache(expire=60)  # Cache for 60 seconds to improve performance.
def list_users(db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user_token)):
    """
    Retrieve a list of all users in the system (Admin only).

    This endpoint verifies that the current user has admin privileges before returning all user records.
    It is intended for administrative purposes only.

    Parameters:
        db (Session): Database session dependency.
        current_user (UserModel): The currently authenticated user obtained via token dependency.

    Returns:
        list[UserOut]: A list of all users formatted according to the UserOut schema.
    """
    # Verify that the current user is an administrator.
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    # Return all users from the database.
    return db.query(UserModel).all()

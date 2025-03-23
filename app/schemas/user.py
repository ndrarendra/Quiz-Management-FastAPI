#####################################
# User Schemas 
# Created By : 마렌드라 라마다니        
# Date : 2025-03-22                 
#####################################

from pydantic import BaseModel, EmailStr
class UserCreate(BaseModel):
    """
    Schema for creating a new user.

    Attributes:
        username (str): The desired username for the new user.
        email (EmailStr): The user's email address (validated as a proper email).
        password (str): The user's raw password, which should be hashed before storage.
    """
    username: str  # The user's chosen username.
    email: EmailStr  # The user's email address, validated by Pydantic.
    password: str  # The raw password; ensure to hash it before saving to the database.


class UserOut(BaseModel):
    """
    Schema for outputting user information.

    Attributes:
        id (int): Unique identifier for the user.
        username (str): The user's username.
        email (EmailStr): The user's email address.
        is_admin (bool): Flag indicating whether the user has administrative privileges.
    """
    id: int  # Unique user identifier.
    username: str  # The user's username.
    email: EmailStr  # The user's email address.
    is_admin: bool  # True if the user is an administrator; otherwise, False.

    class Config:
        # Allows instantiation of the model using an object's attributes (e.g., ORM models)
        from_attributes = True


class Token(BaseModel):
    """
    Schema for an authentication token.

    Attributes:
        access_token (str): The JWT or similar access token.
        token_type (str): The type of the token (e.g., "bearer").
    """
    access_token: str  # The token string used for authentication.
    token_type: str  # The token type (usually "bearer").

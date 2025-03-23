#####################################
# User Database Model 
# Created By : 마렌드라 라마다니        
# Date : 2025-03-22                 
#####################################

from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base

class User(Base):
    """
    Represents a user in the system.

    Attributes:
        id (int): The primary key identifier for the user.
        username (str): The unique username of the user.
        email (str): The unique email address of the user.
        hashed_password (str): The user's password stored in hashed format.
        is_admin (bool): Flag indicating if the user has administrative privileges (defaults to False).
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)  # Unique user identifier.
    username = Column(String, unique=True, index=True, nullable=False)  # Unique username; must be provided.
    email = Column(String, unique=True, index=True, nullable=False)  # Unique email; must be provided.
    hashed_password = Column(String, nullable=False)  # Password stored as a hash for security; required.
    is_admin = Column(Boolean, default=False)  # Indicates admin status; defaults to False.

###########################################
# Utlities for Password and other utilities
# Created By : 마렌드라 라마다니        
# Date : 2025-03-22                 
############################################

from passlib.context import CryptContext

# Set up the password hashing context.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hash the plain text password using bcrypt.
    
    :param password: The plain text password.
    :return: The hashed password.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against the hashed version.
    
    :param plain_password: The plain text password.
    :param hashed_password: The hashed password.
    :return: True if the password is valid, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)
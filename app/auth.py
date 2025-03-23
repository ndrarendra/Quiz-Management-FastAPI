# app/auth.py

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User as UserModel

# OAuth2 / JWT config
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")
SECRET_KEY = os.environ.get("SECRET_KEY", "YOUR_DEFAULT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def get_db():
    """
    Provide a new SQLAlchemy session for each request,
    ensuring we close it afterward.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT (access token).
    - data: the payload dict (commonly includes { "sub": <username> })
    - expires_delta: optional timedelta for token expiry
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user_from_token(token: str, db: Session) -> UserModel:
    """
    Given a JWT token string and a DB session, decode it and
    retrieve the corresponding user. If invalid, raise 401.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user

def get_current_user_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserModel:
    """
    Dependency for endpoints that require a valid token
    from OAuth2PasswordBearer (Authorization header).
    """
    return get_current_user_from_token(token, db)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserModel:
    """
    An alias of get_current_user_token, used similarly.
    """
    return get_current_user_from_token(token, db)

def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)) -> UserModel:
    """
    Dependency for UI-based endpoints that read the `access_token`
    from a cookie. If not present, raise 401.
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return get_current_user_from_token(token, db)

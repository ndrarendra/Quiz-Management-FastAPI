#####################################
# Main Program
# Created By : 마렌드라 라마다니
# Date : 2025-03-22
#####################################

# Import necessary libraries and modules
import uvicorn
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

# Import application-specific modules
from app.database import SessionLocal, engine, Base
from app.models.user import User as UserModel
from app.schemas.user import UserCreate, UserOut, Token
from app.utils import hash_password, verify_password

# Create all tables (recommended to use Alembic for production)
Base.metadata.create_all(bind=engine)

# Setup templates and static files for the application
templates = Jinja2Templates(directory="app/templates")
app = FastAPI(title="Quiz API")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# OAuth2 Configuration and JWT settings
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")
SECRET_KEY = os.environ.get("SECRET_KEY", "YOUR_DEFAULT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Lifespan management to handle application startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all database tables on startup
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        # Check for the existence of an admin user
        admin_user = db.query(UserModel).filter(UserModel.is_admin == True).first()
        if not admin_user:
            print("[INFO] Creating default admin user...")
            # Create a default admin user if not found
            new_admin = UserModel(
                username=os.environ.get("DEFAULT_ADMIN_USERNAME", "admin"),
                email=os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@example.com"),
                hashed_password=hash_password(os.environ.get("DEFAULT_ADMIN_PASSWORD", "admin123")),
                is_admin=True
            )
            db.add(new_admin)
            db.commit()
            print(f"[INFO] Default admin user created: {new_admin.username}")
        else:
            print("[INFO] Admin user already exists.")
    finally:
        db.close()
    yield
    print("[INFO] Application shutdown.")

# Dependency to obtain a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Generate a JWT access token with expiration time
def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Extract and verify the current user from a JWT token
def get_current_user_from_token(token: str, db: Session) -> UserModel:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    # Query the user from the database
    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user

# Dependency to get the current user using OAuth2 token
def get_current_user_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserModel:
    return get_current_user_from_token(token, db)

# Register a new user
@app.post("/users/register", response_model=UserOut)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if username or email already exists
    existing_user = db.query(UserModel).filter((UserModel.username == user.username) | (UserModel.email == user.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    # Create and save the new user
    new_user = UserModel(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Handle user login and token generation
@app.post("/users/login", response_model=Token)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Authenticate user credentials
    db_user = db.query(UserModel).filter(UserModel.username == form_data.username).first()
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    # Generate an access token
    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# Get the details of the currently authenticated user
@app.get("/users/me", response_model=UserOut)
def read_users_me(current_user: UserModel = Depends(get_current_user_token)):
    return current_user

# List all users (Admin access required)
@app.get("/admin/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user_token)):
    # Check if the current user is an admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    # Retrieve and return the list of all users
    return db.query(UserModel).all()

# Run the application with Uvicorn
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

#####################################
# Main Program
# Created By : 마렌드라 라마다니
# Date       : 2025-03-22
#####################################

import uvicorn
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from sqlalchemy.orm import Session

# Application-specific modules
from app.database import SessionLocal, engine, Base
from app.models.user import User as UserModel

from app.utils import hash_password

from app.routers import (
    user_management,
    ui_login,
    admin_users,
    admin_quizzes,
    user_quizzes,
    quiz_retrieval,
    admin_nonui_quiz
)



@asynccontextmanager
async def lifespan(app: FastAPI):
    FastAPICache.init(InMemoryBackend(), prefix="quiz_cache")
    # Create tables on startup (recommended to use Alembic for production)
    #Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        admin_user = db.query(UserModel).filter(UserModel.is_admin == True).first()
        if not admin_user:
            print("[INFO] Creating default admin user...")
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

# Setup templates, static files
app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


app.include_router(user_management.router)
app.include_router(ui_login.router)
app.include_router(admin_users.router)
app.include_router(admin_quizzes.router)
app.include_router(user_quizzes.router)
app.include_router(quiz_retrieval.router)
app.include_router(admin_nonui_quiz.router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

#####################################
# Database Settings for PostgreSQL  
# Created By : 마렌드라 라마다니        
# Date : 2025-03-22                 
#####################################
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Read database credentials from environment variables with default value if not exist
DATABASE_USER = os.environ.get("DB_USER", "user")
DATABASE_PASSWORD = os.environ.get("DB_PASSWORD", "password")
DATABASE_HOST = os.environ.get("DB_HOST", "localhost")
DATABASE_PORT = os.environ.get("DB_PORT", "5432")
DATABASE_NAME = os.environ.get("DB_NAME", "quiz_db")

DATABASE_URL = f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
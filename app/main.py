#####################################
# Main Program
# Created By : 마렌드라 라마다니        
# Date : 2025-03-22                 
#####################################
import uvicorn
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.database import SessionLocal,engine

app = FastAPI(title="Quiz API", docs_url="/docs")

# Mount static files and templates for the UI
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Application Main Point
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
    
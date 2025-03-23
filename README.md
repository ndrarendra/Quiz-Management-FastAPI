# quiz_test
[한국글로벌널리지] 백엔드 개발자 실무 과제


# Quiz Application Setup and Usage Guide

This guide provides clear instructions for setting up and running the Quiz Application smoothly on MacOS.

## Requirements

Before running the application, ensure you have installed the following:

- **Python (Anaconda)**: Version 3.12.8
- **pipx**:
  ```bash
  brew install pipx
  ```
- **Poetry** (installed via pipx):
  ```bash
  pipx install poetry
  ```
- **PostgreSQL**: Version 17 (MacOS Sequoia)

## Initial Setup

### Database
- After installing PostgreSQL, create a database for the application:
  ```
  Database Name: quiz_db
  ```

### Environment Variables
Create a `.env` file inside the `app` directory with the following details. If any of these are omitted, default values will be used:

```env
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=quiz_db
SECRET_KEY=mykey
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123
DEFAULT_ADMIN_EMAIL=admin@example.com
```

## Running the Application
To launch the application, execute the following command from your terminal:

```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Accessing the Application

The application provides both an API interface and a simple UI:

- **API Documentation**: Access detailed API endpoints and explanations:
  ```
  http://127.0.0.1:8000/docs#/
  ```

- **User Interface (UI)**: For testing or demonstration purposes:
  ```
  http://127.0.0.1:8000/ui/login
  ```

## Initial Admin Setup
Upon first run, the application automatically creates an admin account based on your `.env` file. Use these credentials to log in initially.

## Functional Overview

### API Categories
The API endpoints are organized into logical groups:

- **User Management**: CRUD operations for users and login functionality.
- **Admin**: Administrative functionalities.
- **UI**: Endpoints related to user interfaces for both admins and users.
- **Quiz Retrieval**: Endpoints for fetching quizzes.
- **Quiz Attempts**: Managing quiz answers, including autosaving functionality.
- **Quiz Management**: Creating, updating, and deleting quizzes.

### Creating Users and Quizzes
- **Users**:
  - Via UI (login as Admin and use the provided interface)
  - Via API directly (`/user/register`)

- **Quizzes**:
  - Use the provided JSON files (`test_1.json`, `test_2.json`, `test_3.json`) via the API endpoint (`admin/quizzes`).
  - Copy the json data into the API 
  - Set the REQUIRED_NUM_CHOICES in the app/routers/admin_nonui_quiz.py to apply n+2 , The Default is 4.
### Testing Quizzes
- Login as a regular user (Admins cannot attempt quizzes)
- Begin testing by accessing quizzes available through the UI or API.

## Additional Notes
- The provided UI is intentionally simple and is meant primarily for testing and demonstration purposes.
- All API endpoints contain clear descriptions and instructions in English for ease of use.



# app/routers/admin_quizzes.py
import json
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.models.quiz import Quiz, QuizAttempt
from app.auth import get_db,get_current_user_from_cookie
from app.models.user import User as UserModel
from app.config import templates  # now we import from config
router = APIRouter(prefix="/ui/admin", tags=["UI", "Admin"])

@router.get("/", response_class=HTMLResponse, tags=["UI", "Admin"])
def ui_admin_landing(request: Request, db: Session = Depends(get_db)):
    """
    Admin landing page.

    Checks for a current user from a cookie and verifies that the user is an admin.
    If no user is found or the user is not an admin, redirects to the appropriate login or user page.

    Parameters:
        request (Request): The incoming HTTP request.
        db (Session): The database session dependency.

    Returns:
        A TemplateResponse for the admin index page or a RedirectResponse if authentication fails.
    """
    try:
        current_user = get_current_user_from_cookie(request, db)
    except HTTPException:
        # Redirect to login if user is not authenticated.
        return RedirectResponse(url="/ui/login", status_code=302)
    if not current_user.is_admin:
        # Redirect non-admin users to the user interface.
        return RedirectResponse(url="/ui/user", status_code=302)
    # Render the admin landing page.
    return templates.TemplateResponse("/admin/index.html", {
        "request": request,
        "user": current_user
    })

@router.get("/quizzes", response_class=HTMLResponse, tags=["UI", "Admin"])
def ui_admin_quiz_list(request: Request, db: Session = Depends(get_db)):
    """
    Display a paginated list of quizzes for admin.

    Validates that the current user is an admin, then retrieves a subset of quizzes based on
    page and page_size query parameters. It also calculates the total number of pages.

    Parameters:
        request (Request): The incoming HTTP request.
        db (Session): The database session dependency.

    Returns:
        A TemplateResponse rendering the list of quizzes for the admin interface.
    """
    try:
        current_user = get_current_user_from_cookie(request, db)
    except HTTPException:
        # Redirect to login if the user is not authenticated.
        return RedirectResponse(url="/ui/login", status_code=302)
    if not current_user.is_admin:
        # Only admins are allowed to view the quiz list.
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    # Get pagination parameters with defaults.
    page = int(request.query_params.get("page", 1))
    page_size = int(request.query_params.get("page_size", 10))
    
    # Retrieve quizzes with pagination.
    quizzes = db.query(Quiz).offset((page - 1) * page_size).limit(page_size).all()
    total_quizzes = db.query(Quiz).count()
    total_pages = (total_quizzes + page_size - 1) // page_size
    
    return templates.TemplateResponse("/admin/quizzes/list.html", {
        "request": request,
        "quizzes": quizzes,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "user": current_user
    })

@router.get("/quizzes/{quiz_id}/edit", response_class=HTMLResponse, tags=["UI", "Admin"])
def ui_admin_quiz_edit_get(quiz_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Render the quiz editing page for a specific quiz.

    Validates that the current user is an admin, retrieves the quiz by its ID, and constructs
    a dictionary representation of the quiz (including its questions and choices) to be passed to the template.

    Parameters:
        quiz_id (int): The unique identifier of the quiz to edit.
        request (Request): The incoming HTTP request.
        db (Session): The database session dependency.

    Returns:
        A TemplateResponse rendering the quiz edit page.
    """
    try:
        current_user = get_current_user_from_cookie(request, db)
    except HTTPException:
        # Redirect to login if authentication fails.
        return RedirectResponse(url="/ui/login", status_code=302)
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    # Retrieve the quiz from the database.
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Construct quiz data with its questions and choices.
    quiz_data = {
        "title": quiz.title,
        "description": quiz.description,
        "exam_question_count": quiz.exam_question_count,
        "randomize_questions": quiz.randomize_questions,
        "randomize_choices": quiz.randomize_choices,
        "questions": []
    }
    for q in quiz.questions:
        quiz_data["questions"].append({
            "id": q.id,
            "text": q.text,
            "choices": [
                {"id": c.id, "text": c.text, "is_correct": c.is_correct}
                for c in q.choices
            ]
        })
    return templates.TemplateResponse("/admin/quizzes/edit.html", {
        "request": request,
        "quiz": quiz_data,
        "quiz_id": quiz_id,
        "user": current_user
    })

@router.post("/quizzes/{quiz_id}/edit", response_class=HTMLResponse, tags=["UI", "Admin"])
async def ui_admin_quiz_edit_post(quiz_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Process the POST request for editing a quiz.

    Validates admin privileges, parses JSON quiz data from the form, updates quiz details,
    validates each question for a single correct answer, replaces existing questions with new ones,
    and commits the changes to the database.

    Parameters:
        quiz_id (int): The ID of the quiz to be updated.
        request (Request): The incoming HTTP request containing form data.
        db (Session): The database session dependency.

    Returns:
        A RedirectResponse to the quiz list page on success or a TemplateResponse with an error message if validation fails.
    """
    try:
        current_user = get_current_user_from_cookie(request, db)
    except HTTPException:
        return RedirectResponse(url="/ui/login", status_code=302)
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    # Retrieve form data.
    form_data = await request.form()
    quiz_json = form_data.get("quiz_data")
    if not quiz_json:
        return templates.TemplateResponse("/admin/quizzes/edit.html", {
            "request": request,
            "error": "Missing quiz data",
            "user": current_user,
            "quiz_id": quiz_id,
            "quiz": {}
        })
    
    # Parse the JSON quiz data.
    try:
        quiz_payload = json.loads(quiz_json)
    except Exception as e:
        return templates.TemplateResponse("/admin/quizzes/edit.html", {
            "request": request,
            "error": f"Invalid JSON: {e}",
            "user": current_user,
            "quiz_id": quiz_id,
            "quiz": {}
        })
    
    # Retrieve the existing quiz.
    db_quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not db_quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Update quiz properties with the new data.
    db_quiz.title = quiz_payload.get("title", db_quiz.title)
    db_quiz.description = quiz_payload.get("description", db_quiz.description)
    db_quiz.exam_question_count = quiz_payload.get("exam_question_count", db_quiz.exam_question_count)
    db_quiz.randomize_questions = quiz_payload.get("randomize_questions", db_quiz.randomize_questions)
    db_quiz.randomize_choices = quiz_payload.get("randomize_choices", db_quiz.randomize_choices)
    
    # Validate each question has exactly one correct answer.
    for q in quiz_payload.get("questions", []):
        correct_count = sum(1 for c in q.get("choices", []) if c.get("is_correct"))
        if correct_count != 1:
            return templates.TemplateResponse("admin_quiz_edit.html", {
                "request": request,
                "error": f"Question '{q.get('text')}' must have exactly one correct answer",
                "user": current_user,
                "quiz_id": quiz_id,
                "quiz": quiz_payload
            })
    
    # Clear current questions to replace with new ones.
    db_quiz.questions.clear()
    from app.models.quiz import Question, Choice
    for q in quiz_payload.get("questions", []):
        db_question = Question(text=q.get("text"))
        for c in q.get("choices", []):
            db_choice = Choice(
                text=c.get("text"),
                is_correct=c.get("is_correct", False)
            )
            db_question.choices.append(db_choice)
        db_quiz.questions.append(db_question)
    
    db.commit()
    db.refresh(db_quiz)
    return RedirectResponse(url="/ui/admin/quizzes", status_code=302)

@router.get("/quizzes/{quiz_id}/delete", response_class=HTMLResponse, tags=["UI", "Admin"])
def ui_admin_quiz_delete_get(quiz_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Render a confirmation page for quiz deletion.

    Validates admin privileges and retrieves the specified quiz. If found, passes the quiz to the delete template.

    Parameters:
        quiz_id (int): The ID of the quiz to delete.
        request (Request): The incoming HTTP request.
        db (Session): The database session dependency.

    Returns:
        A TemplateResponse for the quiz deletion confirmation page.
    """
    try:
        current_user = get_current_user_from_cookie(request, db)
    except HTTPException:
        return RedirectResponse(url="/ui/login", status_code=302)
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    return templates.TemplateResponse("/admin/quizzes/delete.html", {
        "request": request,
        "quiz": quiz,
        "user": current_user
    })

@router.post("/quizzes/{quiz_id}/delete", response_class=HTMLResponse, tags=["UI", "Admin"])
def ui_admin_quiz_delete_post(quiz_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Process the deletion of a quiz.

    Checks admin privileges, retrieves the quiz, deletes it from the database, and then redirects back to the quiz list.

    Parameters:
        quiz_id (int): The ID of the quiz to be deleted.
        request (Request): The incoming HTTP request.
        db (Session): The database session dependency.

    Returns:
        A RedirectResponse back to the admin quiz list page.
    """
    try:
        current_user = get_current_user_from_cookie(request, db)
    except HTTPException:
        return RedirectResponse(url="/ui/login", status_code=302)
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    db.delete(quiz)
    db.commit()
    return RedirectResponse(url="/ui/admin/quizzes", status_code=302)

@router.get("/quiz_attempts", response_class=HTMLResponse, tags=["UI", "Admin"])
def admin_quiz_attempts(
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user_from_cookie)
):
    """
    Display all quiz attempts for admin review.

    Retrieves all quiz attempts and attempts to parse 'exam_data' and 'answers' fields from JSON strings
    into lists. If parsing fails, defaults to an empty list.

    Parameters:
        request (Request): The incoming HTTP request.
        db (Session): The database session dependency.
        current_user (UserModel): The current admin user (retrieved from cookie).

    Returns:
        A TemplateResponse rendering the admin quiz attempts page.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    # Retrieve all quiz attempts.
    attempts = db.query(QuizAttempt).all()
    
    # Parse the JSON strings into lists for 'exam_data' and 'answers'.
    for attempt in attempts:
        try:
            attempt.exam_data = json.loads(attempt.exam_data) if attempt.exam_data else []
        except Exception:
            attempt.exam_data = []
        try:
            attempt.answers = json.loads(attempt.answers) if attempt.answers else []
        except Exception:
            attempt.answers = []
    
    return templates.TemplateResponse("/admin/quizzes/attempts.html", {
        "request": request,
        "attempts": attempts,
        "user": current_user
    })

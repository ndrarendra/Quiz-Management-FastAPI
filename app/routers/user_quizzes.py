# app/routers/user_quizzes.py
import json
from datetime import datetime

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.models.quiz import Quiz, QuizAttempt,Question
from app.config import templates  # now we import from config
from app.auth import get_db,get_current_user_from_cookie


router = APIRouter(prefix="/ui", tags=["UI"])

@router.get("/user", response_class=HTMLResponse, tags=["UI"])
def ui_user_landing(request: Request, db: Session = Depends(get_db)):
    """
    Render the user landing page.

    This endpoint verifies that a user is logged in via a cookie. If the user is an admin, they are
    redirected to the admin dashboard. Otherwise, it fetches all quizzes and renders the user dashboard.

    Parameters:
        request (Request): The incoming HTTP request.
        db (Session): Database session dependency.

    Returns:
        TemplateResponse: Renders the user landing page with quizzes and user details,
                          or a RedirectResponse if the user is not authenticated or is an admin.
    """
    try:
        current_user = get_current_user_from_cookie(request, db)
    except HTTPException:
        # Redirect to login page if no valid user cookie is found.
        return RedirectResponse(url="/ui/login", status_code=302)
    
    # Redirect admin users to the admin dashboard.
    if current_user.is_admin:
        return RedirectResponse(url="/ui/admin", status_code=302)
    
    # Retrieve all quizzes from the database.
    quizzes = db.query(Quiz).all()
    
    # Render the user dashboard template.
    return templates.TemplateResponse("/users/index.html", {
        "request": request,
        "user": current_user,
        "quizzes": quizzes
    })


@router.get("/", response_class=HTMLResponse, tags=["UI"])
def ui_index(request: Request, db: Session = Depends(get_db)):
    """
    Render the main index page for users.

    This endpoint ensures that the user is logged in and then retrieves all quizzes to be displayed
    on the main index page.

    Parameters:
        request (Request): The incoming HTTP request.
        db (Session): Database session dependency.

    Returns:
        TemplateResponse: Renders the index page with the current user and quizzes.
    """
    try:
        current_user = get_current_user_from_cookie(request, db)
    except HTTPException:
        return RedirectResponse(url="/ui/login", status_code=302)
    
    # Retrieve all quizzes.
    quizzes = db.query(Quiz).all()
    
    # Render the main index template.
    return templates.TemplateResponse("/users/index.html", {
        "request": request,
        "quizzes": quizzes,
        "user": current_user
    })


@router.get("/quiz/{quiz_id}/attempt", response_class=HTMLResponse, tags=["UI"])
def ui_quiz_attempt(quiz_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Render the quiz attempt page for a given quiz.

    This endpoint ensures the user is authenticated and retrieves or creates an active quiz attempt.
    It then parses the exam data and paginates it according to the admin-defined 'questions_per_page'
    setting in the Quiz model.
    """
    # 1) Ensure user is logged in.
    try:
        current_user = get_current_user_from_cookie(request, db)
    except HTTPException:
        return RedirectResponse(url="/ui/login", status_code=302)

    # Retrieve quiz details early so that db_quiz is always available.
    db_quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not db_quiz:
        return RedirectResponse(url="/ui", status_code=302)

    # 2) Retrieve the most recent active quiz attempt (if any).
    attempt = db.query(QuizAttempt).filter(
        QuizAttempt.quiz_id == quiz_id,
        QuizAttempt.user_id == current_user.id
    ).order_by(QuizAttempt.started_at.desc()).first()

    # If no active attempt is found, create a new one.
    if not attempt:
        # Use the already retrieved db_quiz
        all_questions = db_quiz.questions
        exam_data = []
        for q in all_questions:
            exam_data.append({
                "question_id": q.id,
                "text": q.text,
                "choices": [
                    {"choice_id": c.id, "text": c.text}
                    for c in q.choices
                ]
            })
        new_attempt = QuizAttempt(
            quiz_id=quiz_id,
            user_id=current_user.id,
            exam_data=json.dumps(exam_data)
        )
        db.add(new_attempt)
        db.commit()
        db.refresh(new_attempt)
        attempt = new_attempt

    # 3) Block re-opening if the attempt has already been submitted.
    if attempt.submitted_at is not None:
        return HTMLResponse(
            "<h1>This quiz has already been submitted. No further attempts allowed.</h1>",
            status_code=403
        )

    # 4) Parse the exam_data from JSON.
    try:
        exam_data = json.loads(attempt.exam_data)
    except Exception:
        exam_data = []

    try:
        saved_answers = json.loads(attempt.answers) if attempt.answers else []
    except Exception:
        saved_answers = []
    # 5) Pagination Logic Using Admin-Defined Questions Per Page:
    page = int(request.query_params.get("page", 1))
    # Use the admin's setting; fallback to 10 if not set.
    page_size = db_quiz.questions_per_page if db_quiz.questions_per_page else 10
    total = len(exam_data)
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    paginated_questions = exam_data[start:start + page_size]

    # Render the quiz attempt template.
    return templates.TemplateResponse("/users/attempt_quiz.html", {
        "request": request,
        "quiz": db_quiz,
        "exam_data": paginated_questions,
        "user": current_user,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "saved_answers": saved_answers  
    })



@router.post("/quiz/{quiz_id}/submit", response_class=HTMLResponse, tags=["UI"])
async def ui_quiz_submit(quiz_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Process the submission of a quiz attempt.

    This endpoint handles the final submission of a quiz attempt. It first ensures the user is authenticated
    and retrieves the active attempt. It then parses the form data for answers, performs grading by comparing
    submitted answers with the correct choices from the database, updates the attempt with the score and submission
    timestamp, and finally renders a result page.

    Parameters:
        quiz_id (int): The unique identifier of the quiz.
        request (Request): The incoming HTTP request containing form data.
        db (Session): Database session dependency.

    Returns:
        TemplateResponse: Renders the result page with the final score,
                          or an HTMLResponse if no active attempt is found or the attempt is already submitted.
    """
    try:
        current_user = get_current_user_from_cookie(request, db)
    except HTTPException:
        return RedirectResponse(url="/ui/login", status_code=302)

    # 1) Retrieve the most recent active quiz attempt.
    attempt = db.query(QuizAttempt).filter(
        QuizAttempt.quiz_id == quiz_id,
        QuizAttempt.user_id == current_user.id
    ).order_by(QuizAttempt.started_at.desc()).first()

    if not attempt:
        return HTMLResponse("<h2>No active quiz attempt found.</h2>", status_code=404)

    # 2) Block resubmission if the attempt has already been submitted.
    if attempt.submitted_at is not None:
        return HTMLResponse(
            "<h2>This quiz has already been submitted. Re-submission not allowed.</h2>",
            status_code=403
        )

    # 3) Parse form data for final answers.
    form_data = await request.form()
    answers = []
    # Expect keys in the form "answer_{question_id}" with the value being the chosen choice_id.
    for key, value in form_data.items():
        if key.startswith("answer_"):
            question_id = int(key.split("_")[1])
            choice_id = int(value)
            answers.append({"question_id": question_id, "choice_id": choice_id})

    # 4) Final grading: calculate score based on correct answers.
    total_score = 0
    for ans in answers:
        # Retrieve the question from the database.
        question = db.query(Question).filter(Question.id == ans["question_id"]).first()
        if question:
            # Identify the correct choice for the question.
            correct_choice = next((c for c in question.choices if c.is_correct), None)
            # If the submitted answer matches the correct choice, increment the score.
            if correct_choice and correct_choice.id == ans["choice_id"]:
                total_score += 1

    # 5) Update the quiz attempt as submitted, storing answers and score.
    attempt.answers = json.dumps(answers)
    attempt.score = total_score
    attempt.submitted_at = datetime.utcnow()
    db.commit()
    db.refresh(attempt)

    # Render the result page showing the final score.
    return templates.TemplateResponse("/users/result.html", {
        "request": request,
        "score": total_score,
        "user": current_user
    })

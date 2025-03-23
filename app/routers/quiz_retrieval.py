# app/routers/admin_quizzes.py
import random
import json
from datetime import datetime
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi import Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.models.quiz import Quiz, QuizAttempt
from app.auth import get_current_user,get_db,get_current_user_from_cookie
from app.models.user import User as UserModel
from fastapi_cache.decorator import cache
from app.schemas.quiz import (
    QuizOut, QuizDetailOut, QuizAttemptOut, QuizSubmit
)

router = APIRouter(prefix="/ui/admin", tags=["UI", "Admin"])


@router.get("/quizzes", response_model=list[QuizOut], tags=["Quiz Retrieval"])
@cache(expire=60)  # Cache the list of quizzes for 60 seconds to improve performance.
def list_quizzes(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Retrieve a paginated list of quizzes.

    This endpoint fetches quizzes from the database using pagination parameters and caches the results for 60 seconds.

    Parameters:
        page (int): The current page number (default is 1). Must be greater than or equal to 1.
        page_size (int): The number of quizzes per page (default is 10). Must be greater than or equal to 1.
        db (Session): Database session dependency.
        current_user (UserModel): The currently authenticated user.

    Returns:
        list[QuizOut]: A list of quizzes in the format defined by the QuizOut schema.
    """
    quizzes = db.query(Quiz).offset((page - 1) * page_size).limit(page_size).all()
    return quizzes

@router.get("/quizzes/{quiz_id}", response_model=QuizDetailOut, tags=["Quiz Retrieval"])
def get_quiz_detail(
    quiz_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Retrieve detailed information for a specific quiz with paginated questions.

    This endpoint returns a detailed view of a quiz. It selects a subset of questions based on the exam_question_count,
    optionally randomizes questions and choices, and then applies pagination.

    Parameters:
        quiz_id (int): The unique identifier of the quiz.
        page (int): The current page number for question pagination (default: 1).
        page_size (int): The number of questions per page (default: 10).
        db (Session): Database session dependency.
        current_user (UserModel): The currently authenticated user.

    Returns:
        QuizDetailOut: A detailed view of the quiz including paginated questions.
    """
    db_quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not db_quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Determine the set of questions to use for the exam.
    if len(db_quiz.questions) > db_quiz.exam_question_count:
        questions = random.sample(db_quiz.questions, db_quiz.exam_question_count)
    else:
        questions = db_quiz.questions

    # Randomize question order if the setting is enabled.
    if db_quiz.randomize_questions:
        random.shuffle(questions)
    
    # Calculate pagination details.
    total = len(questions)
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    paginated_questions = questions[start:start + page_size]
    
    # Process each question and randomize its choices if needed.
    questions_out = []
    for q in paginated_questions:
        choices = q.choices.copy()
        if db_quiz.randomize_choices:
            random.shuffle(choices)
        questions_out.append({
            "id": q.id,
            "text": q.text,
            "choices": [{"choice_id": c.id, "text": c.text} for c in choices]
        })
    
    return QuizDetailOut(
        id=db_quiz.id,
        title=db_quiz.title,
        description=db_quiz.description,
        questions=questions_out,
        total_questions=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.post("/quizzes/{quiz_id}/attempt", response_model=QuizAttemptOut, tags=["Quiz Attempt"])
def start_quiz_attempt(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Start a new quiz attempt or return an existing active attempt.

    This endpoint checks if there is an active (not yet submitted) quiz attempt for the current user.
    If found, it returns the active attempt. Otherwise, it creates a new quiz attempt by selecting and
    optionally randomizing questions and choices, and stores the exam data.

    Parameters:
        quiz_id (int): The unique identifier of the quiz.
        db (Session): Database session dependency.
        current_user (UserModel): The currently authenticated user.

    Returns:
        QuizAttemptOut: The quiz attempt details including exam data and existing answers if any.
    """
    # Check for an existing active quiz attempt.
    attempt = db.query(QuizAttempt).filter(
        QuizAttempt.quiz_id == quiz_id,
        QuizAttempt.user_id == current_user.id,
        QuizAttempt.submitted_at.is_(None)
    ).first()
    if attempt:
        return QuizAttemptOut(
            id=attempt.id,
            quiz_id=attempt.quiz_id,
            user_id=attempt.user_id,
            started_at=attempt.started_at,
            submitted_at=attempt.submitted_at,
            score=attempt.score,
            exam_data=json.loads(attempt.exam_data),
            answers=json.loads(attempt.answers) if attempt.answers else None
        )
    
    # Retrieve the quiz.
    db_quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not db_quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    if not db_quiz.questions:
        raise HTTPException(status_code=400, detail="Quiz has no questions")
    
    # Select questions based on the exam_question_count setting.
    if len(db_quiz.questions) > db_quiz.exam_question_count:
        selected_questions = random.sample(db_quiz.questions, db_quiz.exam_question_count)
    else:
        selected_questions = db_quiz.questions

    # Randomize question order if enabled.
    if db_quiz.randomize_questions:
        random.shuffle(selected_questions)
    
    # Build exam data including questions and their choices.
    exam_data = []
    for q in selected_questions:
        choices = q.choices.copy()
        if db_quiz.randomize_choices:
            random.shuffle(choices)
        exam_data.append({
            "question_id": q.id,
            "text": q.text,
            "choices": [{"choice_id": c.id, "text": c.text} for c in choices]
        })
    
    # Create and persist a new quiz attempt.
    new_attempt = QuizAttempt(
        quiz_id=quiz_id,
        user_id=current_user.id,
        exam_data=json.dumps(exam_data)
    )
    db.add(new_attempt)
    db.commit()
    db.refresh(new_attempt)
    
    return QuizAttemptOut(
        id=new_attempt.id,
        quiz_id=new_attempt.quiz_id,
        user_id=new_attempt.user_id,
        started_at=new_attempt.started_at,
        submitted_at=new_attempt.submitted_at,
        score=new_attempt.score,
        exam_data=json.loads(new_attempt.exam_data),
        answers=json.loads(new_attempt.answers) if new_attempt.answers else None
    )

@router.post("/quizzes/{quiz_id}/submit", response_model=QuizAttemptOut, tags=["Quiz Attempt"])
def submit_quiz_attempt(
    quiz_id: int,
    submission: QuizSubmit,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Submit a completed quiz attempt.

    This endpoint processes the quiz submission by validating each answer, computing the total score,
    marking the attempt as submitted, and returning the updated quiz attempt.

    Parameters:
        quiz_id (int): The unique identifier of the quiz.
        submission (QuizSubmit): The submission payload containing the list of answers.
        db (Session): Database session dependency.
        current_user (UserModel): The currently authenticated user.

    Returns:
        QuizAttemptOut: The updated quiz attempt, including the computed score and submission details.
    """
    # Retrieve the most recent active quiz attempt.
    attempt = db.query(QuizAttempt).filter(
        QuizAttempt.quiz_id == quiz_id,
        QuizAttempt.user_id == current_user.id,
        QuizAttempt.submitted_at.is_(None)
    ).order_by(QuizAttempt.started_at.desc()).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="No active quiz attempt found")
    
    # Save the submitted answers.
    attempt.answers = json.dumps([a.dict() for a in submission.answers])
    
    # Calculate the total score based on correct answers.
    total_score = 0
    for ans in submission.answers:
        from app.models.quiz import Question
        question = db.query(Question).filter(Question.id == ans.question_id).first()
        if question:
            correct_choice = next((c for c in question.choices if c.is_correct), None)
            if correct_choice and correct_choice.id == ans.choice_id:
                total_score += 1
    attempt.score = total_score
    
    # Mark the attempt as submitted.
    attempt.submitted_at = datetime.utcnow()
    db.commit()
    db.refresh(attempt)
    
    return QuizAttemptOut(
        id=attempt.id,
        quiz_id=attempt.quiz_id,
        user_id=attempt.user_id,
        started_at=attempt.started_at,
        submitted_at=attempt.submitted_at,
        score=attempt.score,
        exam_data=json.loads(attempt.exam_data),
        answers=json.loads(attempt.answers)
    )

@router.post("/quizzes/{quiz_id}/autosave", response_model=QuizAttemptOut, tags=["Quiz Attempt"])
def autosave_quiz_attempt(
    quiz_id: int,
    submission: QuizSubmit,   # Pydantic model containing answers: List[AnswerSubmit]
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Autosave a quiz attempt's progress.

    This endpoint allows a user to autosave their quiz attempt by merging new answers from the submission
    with any previously saved answers. It supports partial submissions without finalizing the attempt.

    Parameters:
        quiz_id (int): The unique identifier of the quiz.
        submission (QuizSubmit): The autosave submission payload containing answers.
        request (Request): The incoming HTTP request.
        db (Session): Database session dependency.

    Returns:
        QuizAttemptOut: The updated quiz attempt with merged autosaved answers.
    """
    current_user = get_current_user_from_cookie(request, db)
    
    # Retrieve the active quiz attempt.
    attempt = db.query(QuizAttempt).filter(
        QuizAttempt.quiz_id == quiz_id,
        QuizAttempt.user_id == current_user.id,
        QuizAttempt.submitted_at.is_(None)
    ).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="No active quiz attempt found")
    
    # Load existing answers if available.
    existing_answers = []
    if attempt.answers:
        try:
            existing_answers = json.loads(attempt.answers)
        except Exception:
            existing_answers = []
    
    # Convert existing answers to a dictionary for easier merging.
    existing_dict = {item["question_id"]: item["choice_id"] for item in existing_answers}
    
    # Merge new answers from the submission.
    for ans in submission.answers:
        existing_dict[ans.question_id] = ans.choice_id
    
    # Rebuild the merged answers list.
    merged_answers = [{"question_id": qid, "choice_id": cid} for qid, cid in existing_dict.items()]
    
    # Update the attempt with merged answers.
    attempt.answers = json.dumps(merged_answers)
    db.commit()
    db.refresh(attempt)
    
    return QuizAttemptOut(
        id=attempt.id,
        quiz_id=attempt.quiz_id,
        user_id=attempt.user_id,
        started_at=attempt.started_at,
        submitted_at=attempt.submitted_at,
        score=attempt.score,
        exam_data=json.loads(attempt.exam_data),
        answers=json.loads(attempt.answers)
    )

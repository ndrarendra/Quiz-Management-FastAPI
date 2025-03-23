# app/routers/admin_quizzes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.quiz import Quiz, QuizAttempt
from app.models.user import User as UserModel
from app.auth import get_current_user, get_db  # or wherever get_current_user is defined
from app.schemas.quiz import QuizCreate, QuizOut

# Constant defining the required number of choices for each question.
REQUIRED_NUM_CHOICES = 4  # Alternatively, import this constant from a dedicated constants file if needed.

# Define the router for admin quiz management endpoints.
router = APIRouter(prefix="/admin/quizzes", tags=["Admin", "Quiz Management"])

@router.post("/", response_model=QuizOut, status_code=201, tags=["Admin", "Quiz Management"])
def create_quiz(
    quiz: QuizCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Create a new quiz with questions and choices.

    Validates that:
      - The current user is an admin.
      - Each question has exactly REQUIRED_NUM_CHOICES choices.
      - Each question has exactly one correct answer.

    Parameters:
        quiz (QuizCreate): The quiz data containing title, description, exam settings, and questions.
        db (Session): The database session dependency.
        current_user (UserModel): The current user (must be admin).

    Returns:
        The newly created quiz, as represented by the QuizOut schema.
    """
    # Ensure the current user has admin privileges.
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    # Validate each question for the correct number of choices and exactly one correct answer.
    for q in quiz.questions:
        if len(q.choices) != REQUIRED_NUM_CHOICES:
            raise HTTPException(
                status_code=400,
                detail=f"Question '{q.text}' must have exactly {REQUIRED_NUM_CHOICES} choices"
            )
        correct_count = sum(1 for c in q.choices if c.is_correct)
        if correct_count != 1:
            raise HTTPException(
                status_code=400,
                detail=f"Question '{q.text}' must have exactly one correct answer"
            )
    
    # Create a new Quiz instance from the provided quiz data.
    db_quiz = Quiz(
        title=quiz.title,
        description=quiz.description,
        exam_question_count=quiz.exam_question_count,
        randomize_questions=quiz.randomize_questions,
        randomize_choices=quiz.randomize_choices,
    )
    
    # Import the related models for questions and choices.
    from app.models.quiz import Question, Choice

    # Process each question and its choices.
    for q in quiz.questions:
        # Create a new Question instance.
        db_question = Question(text=q.text)
        for c in q.choices:
            # Create a new Choice instance and append it to the question.
            db_choice = Choice(text=c.text, is_correct=c.is_correct)
            db_question.choices.append(db_choice)
        # Append the fully built question to the quiz.
        db_quiz.questions.append(db_question)
    
    # Add the new quiz to the session, commit the transaction, and refresh to get the new data.
    db.add(db_quiz)
    db.commit()
    db.refresh(db_quiz)
    
    # Return the created quiz.
    return db_quiz

@router.put("/{quiz_id}", response_model=QuizOut, tags=["Admin", "Quiz Management"])
def update_quiz(
    quiz_id: int,
    quiz: QuizCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Update an existing quiz with new data.

    Validates that:
      - The current user is an admin.
      - The quiz exists.
      - Each updated question has exactly REQUIRED_NUM_CHOICES choices.
      - Each updated question has exactly one correct answer.

    Parameters:
        quiz_id (int): The ID of the quiz to update.
        quiz (QuizCreate): The new quiz data.
        db (Session): The database session dependency.
        current_user (UserModel): The current user (must be admin).

    Returns:
        The updated quiz, as represented by the QuizOut schema.
    """
    # Check admin privileges.
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    # Retrieve the existing quiz from the database.
    db_quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not db_quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Validate each updated question.
    for q in quiz.questions:
        if len(q.choices) != REQUIRED_NUM_CHOICES:
            raise HTTPException(
                status_code=400,
                detail=f"Question '{q.text}' must have exactly {REQUIRED_NUM_CHOICES} choices"
            )
        correct_count = sum(1 for c in q.choices if c.is_correct)
        if correct_count != 1:
            raise HTTPException(
                status_code=400,
                detail=f"Question '{q.text}' must have exactly one correct answer"
            )
    
    # Update quiz-level attributes.
    db_quiz.title = quiz.title
    db_quiz.description = quiz.description
    db_quiz.exam_question_count = quiz.exam_question_count
    db_quiz.randomize_questions = quiz.randomize_questions
    db_quiz.randomize_choices = quiz.randomize_choices
    
    # Clear existing questions to update them with the new set.
    db_quiz.questions.clear()
    
    from app.models.quiz import Question, Choice

    # Add new questions and their choices.
    for q in quiz.questions:
        db_question = Question(text=q.text)
        for c in q.choices:
            db_choice = Choice(text=c.text, is_correct=c.is_correct)
            db_question.choices.append(db_choice)
        db_quiz.questions.append(db_question)
    
    # Commit the changes and refresh the quiz instance.
    db.commit()
    db.refresh(db_quiz)
    
    return db_quiz

@router.delete("/{quiz_id}", status_code=204, tags=["Admin", "Quiz Management"])
def delete_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Delete a quiz from the database.

    Validates that:
      - The current user is an admin.
      - The quiz exists.

    Parameters:
        quiz_id (int): The ID of the quiz to delete.
        db (Session): The database session dependency.
        current_user (UserModel): The current user (must be admin).

    Returns:
        A JSON response with a success detail message.
    """
    # Ensure the user is an admin.
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    # Retrieve the quiz to be deleted.
    db_quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not db_quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Delete the quiz and commit the change.
    db.delete(db_quiz)
    db.commit()
    
    return {"detail": "Quiz deleted successfully"}

@router.put("/{attempt_id}/reopen", tags=["Admin", "Quiz Management"])
def admin_reopen_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Re-open a quiz attempt by resetting the submitted timestamp.

    This endpoint allows an admin to set the `submitted_at` field of a quiz attempt back to None,
    effectively re-opening the attempt for further modifications or re-grading.

    Parameters:
        attempt_id (int): The ID of the quiz attempt to re-open.
        db (Session): The database session dependency.
        current_user (UserModel): The current user (must be admin).

    Returns:
        A JSON response with a success detail message.
    """
    # Check if the current user is an admin.
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    # Retrieve the quiz attempt from the database.
    attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="No such attempt")
    
    # Reset the submitted_at field to re-open the attempt.
    attempt.submitted_at = None
    db.commit()
    
    return {"detail": "Attempt re-opened by admin."}

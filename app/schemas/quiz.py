#####################################
# Quiz Schemas 
# Created By : 마렌드라 라마다니        
# Date : 2025-03-22                 
#####################################

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# -------------------------------------------------------------------
# Schemas for quiz creation
# -------------------------------------------------------------------

class ChoiceCreate(BaseModel):
    """
    Schema for creating an answer choice for a quiz question.

    Attributes:
        text (str): The content of the answer choice.
        is_correct (bool): A flag indicating whether this choice is the correct answer.
    """
    text: str  # The text for the answer choice.
    is_correct: bool  # True if this choice is the correct answer, False otherwise.

class QuestionCreate(BaseModel):
    """
    Schema for creating a quiz question.

    Attributes:
        text (str): The text of the quiz question.
        choices (List[ChoiceCreate]): A list of possible answer choices for the question.
    """
    text: str  # The question text.
    choices: List[ChoiceCreate]  # A list of choices, each following the ChoiceCreate schema.

class QuizCreate(BaseModel):
    """
    Schema for creating a new quiz.

    Attributes:
        title (str): The title of the quiz.
        description (Optional[str]): A short description of the quiz (optional).
        exam_question_count (int): Number of questions to include in the exam version (default is 10).
        randomize_questions (bool): If True, the questions are randomized when presented (default is True).
        randomize_choices (bool): If True, the choices within each question are randomized (default is True).
        questions (List[QuestionCreate]): A list of quiz questions.
    """
    title: str  # Title of the quiz.
    description: Optional[str] = None  # Optional description of the quiz.
    exam_question_count: int = 10  # Number of questions to be used in the exam.
    randomize_questions: bool = True  # Flag to randomize the order of questions.
    randomize_choices: bool = True  # Flag to randomize the order of answer choices.
    questions: List[QuestionCreate]  # List of questions for the quiz.

# -------------------------------------------------------------------
# Schemas for outputting quiz data
# -------------------------------------------------------------------

class QuizOut(BaseModel):
    """
    Schema for the basic output representation of a quiz.

    Attributes:
        id (int): Unique identifier of the quiz.
        title (str): The quiz title.
        description (Optional[str]): A brief description of the quiz (if provided).
        exam_question_count (int): Number of questions set aside for the exam.
        randomize_questions (bool): Indicates whether questions are randomized.
        randomize_choices (bool): Indicates whether choices are randomized.
    """
    id: int  # Unique identifier for the quiz.
    title: str  # Title of the quiz.
    description: Optional[str]  # Optional description of the quiz.
    exam_question_count: int  # Number of questions for the exam.
    randomize_questions: bool  # Whether questions should be randomized.
    randomize_choices: bool  # Whether choices should be randomized.

    class Config:
        from_attributes = True  # Enable creating this model from ORM object attributes.

class QuizDetailOut(BaseModel):
    """
    Detailed schema for a quiz view including paginated questions.

    Attributes:
        id (int): Unique identifier of the quiz.
        title (str): The quiz title.
        description (Optional[str]): A brief description of the quiz (if provided).
        questions (List[dict]): A list of questions, each represented as a dictionary.
        total_questions (int): Total number of questions available in the quiz.
        page (int): Current page number in a paginated view.
        page_size (int): Number of questions per page.
        total_pages (int): Total number of pages calculated from the question count.
    """
    id: int  # Unique identifier for the quiz.
    title: str  # Title of the quiz.
    description: Optional[str]  # Optional description.
    questions: List[dict]  # List of question data as dictionaries.
    total_questions: int  # Total available questions in the quiz.
    page: int  # Current page number.
    page_size: int  # Number of questions per page.
    total_pages: int  # Total pages available based on total_questions and page_size.

    class Config:
        from_attributes = True  # Allows model instantiation from ORM object attributes.

# -------------------------------------------------------------------
# Schemas for quiz attempt and submission
# -------------------------------------------------------------------

class QuizAttemptOut(BaseModel):
    """
    Schema representing a user's quiz attempt.

    Attributes:
        id (int): Unique identifier for the quiz attempt.
        quiz_id (int): Identifier of the quiz being attempted.
        user_id (int): Identifier of the user taking the quiz.
        started_at (datetime): Timestamp when the quiz attempt began.
        submitted_at (Optional[datetime]): Timestamp when the attempt was submitted (if applicable).
        score (Optional[int]): The score achieved in the quiz attempt (optional).
        exam_data (List[dict]): List of dictionaries containing exam-related data.
        answers (Optional[List[dict]]): List of dictionaries representing the submitted answers.
    """
    id: int  # Unique identifier for the quiz attempt.
    quiz_id: int  # The ID of the quiz being attempted.
    user_id: int  # The ID of the user taking the quiz.
    started_at: datetime  # The start time of the quiz attempt.
    submitted_at: Optional[datetime]  # The submission time (if the quiz has been submitted).
    score: Optional[int]  # The score for this attempt (if graded).
    exam_data: List[dict]  # List of exam-related data dictionaries.
    answers: Optional[List[dict]]  # List of answers submitted by the user.

    class Config:
        from_attributes = True  # Allows instantiation from ORM object attributes.

class AnswerSubmit(BaseModel):
    """
    Schema for submitting an answer to a single question.

    Attributes:
        question_id (int): Identifier of the question being answered.
        choice_id (int): Identifier of the selected answer choice.
    """
    question_id: int  # The ID of the question.
    choice_id: int  # The ID of the selected choice.

class QuizSubmit(BaseModel):
    """
    Schema for submitting a complete set of answers for a quiz.

    Attributes:
        answers (List[AnswerSubmit]): A list of answers, each following the AnswerSubmit schema.
    """
    answers: List[AnswerSubmit]  # List of answer submissions.

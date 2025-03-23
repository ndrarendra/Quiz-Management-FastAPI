#####################################
# Quiz Database Model 
# Created By : 마렌드라 라마다니        
# Date : 2025-03-22                 
#####################################

# app/models/quiz.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
class Quiz(Base):
    """
    Represents a quiz.

    Attributes:
        id (int): Unique identifier for the quiz.
        title (str): The title of the quiz.
        description (str): A brief description of the quiz.
        exam_question_count (int): Number of questions to include in the exam version (default is 10).
        randomize_questions (bool): Flag indicating if questions should be presented in a random order.
        randomize_choices (bool): Flag indicating if choices within each question should be randomized.
        questions (list[Question]): A list of related Question objects associated with the quiz.
    """
    __tablename__ = "quizzes"
    id = Column(Integer, primary_key=True, index=True)  # Primary key with an index for faster lookup.
    title = Column(String, nullable=False)  # Quiz title; cannot be null.
    description = Column(String, nullable=True)  # Optional description of the quiz.
    exam_question_count = Column(Integer, default=10)  # Default number of questions for the exam version.
    randomize_questions = Column(Boolean, default=True)  # Whether to randomize question order.
    randomize_choices = Column(Boolean, default=True)  # Whether to randomize choice order.
    questions_per_page = Column(Integer, default=10) # field for pagination

    quiz_attempts = relationship(
        "QuizAttempt",
        back_populates="quiz",
        cascade="all, delete-orphan",
        passive_deletes=True        
    )
    questions = relationship(
        "Question",
        back_populates="quiz",
        cascade="all, delete-orphan",  # Delete all questions if the quiz is deleted.
        passive_deletes=True
    )
    


class Question(Base):
    """
    Represents a question within a quiz.

    Attributes:
        id (int): Unique identifier for the question.
        quiz_id (int): Foreign key linking the question to its parent quiz.
        text (str): The text of the question.
        choices (list[Choice]): A list of related Choice objects for this question.
        quiz (Quiz): The parent Quiz object.
    """
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)  # Primary key with an index.
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)  
    # Foreign key to the quizzes table; cascades deletes.
    text = Column(Text, nullable=False)  # The question text; cannot be null.
    choices = relationship(
        "Choice",
        back_populates="question",
        cascade="all, delete-orphan",  # Delete all choices if the question is deleted.
        passive_deletes=True
    )
    quiz = relationship("Quiz", back_populates="questions")  # Back-reference to the parent quiz.


class Choice(Base):
    """
    Represents an answer choice for a question.

    Attributes:
        id (int): Unique identifier for the choice.
        question_id (int): Foreign key linking the choice to its parent question.
        text (str): The text of the choice.
        is_correct (bool): Indicates whether this choice is the correct answer.
        question (Question): The parent Question object.
    """
    __tablename__ = "choices"
    id = Column(Integer, primary_key=True, index=True)  # Primary key with an index.
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    # Foreign key to the questions table; cascades deletes.
    text = Column(Text, nullable=False)  # The choice text; cannot be null.
    is_correct = Column(Boolean, default=False)  # Flag to mark the correct choice; defaults to False.
    question = relationship("Question", back_populates="choices")  # Back-reference to the parent question.


class QuizAttempt(Base):
    """
    Represents an attempt by a user to complete a quiz.

    Attributes:
        id (int): Unique identifier for the quiz attempt.
        quiz_id (int): Foreign key linking the attempt to the associated quiz.
        user_id (int): Identifier of the user who made the attempt.
        started_at (datetime): Timestamp when the attempt was started.
        submitted_at (datetime): Timestamp when the attempt was submitted (optional).
        score (int): The score achieved in this attempt (optional).
        exam_data (str): JSON string storing the selected questions and their order/choices.
        answers (str): JSON string storing the user's submitted answers (optional).
    """
    __tablename__ = "quiz_attempts"
    id = Column(Integer, primary_key=True, index=True)  # Primary key with an index.
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)  # Link to the quiz.
    user_id = Column(Integer)  # Ideally, this should be a foreign key to a User table.
    started_at = Column(DateTime, default=datetime.utcnow)  # When the attempt started.
    submitted_at = Column(DateTime, nullable=True)  # When the attempt was submitted; null if not submitted.
    score = Column(Integer, nullable=True)  # Score for the attempt; optional.
    exam_data = Column(Text)  # JSON string containing the selected questions and choices order.
    answers = Column(Text, nullable=True)  # JSON string containing the user's answers.
    quiz = relationship("Quiz", back_populates="quiz_attempts")
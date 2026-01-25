# --------------- IMPORTS --------------
from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.learning.models import (
    LearningProgress, 
    ExerciseAttempt
)

from apps.learning.selectors import (
    load_learning_content,
    get_language,
    get_exercise,
    learning_progress_get,
)

# ------------------- HELPERS (Private functions) -------------------

# --------- Helper 1: Normalize code strings for comparison 
def _normalize_code(user_code: str) -> str:
    """
    Trims leading/trailing whitespace, normalizes newline characters to Unix format, 
    and removes trailing spaces from individual lines.

    Args:
        user_code (str): The raw code string submitted by the user or from storage.

    Returns:
        str: The cleaned and normalized code string.
    """
    text = (user_code or "").strip().replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines).strip()

# --------- Helper 2: Normalize SQL specific syntax
def _normalize_sql(user_code: str) -> str:
    """
    Normalizes SQL queries by collapsing whitespace and converting to uppercase.

    This ensures that SQL comparisons are case-insensitive and ignore minor 
    formatting differences (like extra spaces or tabs), which is standard for MVPs.

    Args:
        user_code (str): The raw SQL query string.

    Returns:
        str: A single-line, uppercase, normalized SQL string.
    """
    text = _normalize_code(user_code)
    text = " ".join(text.split())  # collapse whitespace
    return text.upper()

# ---------------------- SERVICES ----------------------

# ------- Service 1: Initialize a new learning progress record
@transaction.atomic
def learning_progress_start(*, user, language_slug: str) -> LearningProgress:
    """
    Creates a fresh LearningProgress entry for a user starting a new language.

    This service initializes all tracking metrics, including timestamps and empty 
    completion lists, providing a baseline for future attempts.

    Args:
        user (User): The user starting the language track.
        language_slug (str): The slug of the language track being initiated.

    Returns:
        LearningProgress: The newly created progress instance.
    """
    now = timezone.now()
    return LearningProgress.objects.create(
        user=user,
        language_slug=language_slug,
        started_at=now,
        last_activity_at=now,
        current_exercise_id="",
        completed_exercise_ids=[],
        completion_percentage=Decimal("0.00"),
    )


# ----- Service 2: Service 2: Process an exercise submission and update progress
@transaction.atomic
def exercise_submit_attempt(
    *,
    user,
    language_slug: str,
    exercise_id: str,
    user_code: str,
) -> ExerciseAttempt:
    """
    Handles the end-to-end logic for submitting an exercise attempt.

    This service performs four key actions:
    1. Validates the submission against the expected solution (JSON-based).
    2. Calculates the score and status (passed/failed).
    3. Updates or creates the user's LearningProgress, recalculating completion percentage.
    4. Persists the ExerciseAttempt record for history tracking.

    Args:
        user (User): The user submitting the code.
        language_slug (str): The slug of the language for the exercise.
        exercise_id (str): The unique ID of the exercise being attempted.
        user_code (str): The code provided by the user.

    Raises:
        ValueError: If the language, exercise, or expected solution is missing.

    Returns:
        ExerciseAttempt: The record of the attempt with calculated status and feedback.
    """
    
    # Fetch the data (expected_code field specifically) from JSON file
    content = load_learning_content()
    language = get_language(content, language_slug)
    if not language:
        raise ValueError("Language not found")

    exercise = get_exercise(language, exercise_id)
    if not exercise:
        raise ValueError("Exercise not found")

    expected_code = exercise.get("expected_code", "")
    if not expected_code:
        raise ValueError("Exercise has no expected_code")

    # Normalize and compare user input against the expected solution
    if language_slug == "sql":
        expected = _normalize_sql(expected_code)
        actual = _normalize_sql(user_code)
    else:
        expected = _normalize_code(expected_code)
        actual = _normalize_code(user_code)

    # If both outputs match calculate results: status, score, and feedback message
    passed = actual == expected
    status_value = "passed" if passed else "failed"
    score_value = Decimal("100.00") if passed else Decimal("0.00")
    message_value = "Correct ✅" if passed else "Incorrect ❌"

    # ---- Read progress via selector ----
    progress = learning_progress_get(user=user, language_slug=language_slug)
    if not progress: # If not found, create a new one
        progress = learning_progress_start(user=user, language_slug=language_slug)

    now = timezone.now()

    # ---- Update progress state (In LearningProgress Model)  ----
    progress.last_activity_at = now
    progress.current_exercise_id = exercise_id

    if passed:
        completed = list(progress.completed_exercise_ids or [])
        if exercise_id not in completed:
            completed.append(exercise_id)
        progress.completed_exercise_ids = completed

    total_exercises = len(language.get("exercises", [])) or 1
    completed_count = len(progress.completed_exercise_ids or [])

    progress.completion_percentage = (Decimal(completed_count) / Decimal(total_exercises)) * Decimal("100.00")
    progress.save(update_fields=[
        "last_activity_at",
        "current_exercise_id",
        "completed_exercise_ids",
        "completion_percentage",
        "updated_at",
    ])

    # ---- Create attempt record (ExerciseAttempt Model) ----
    attempt = ExerciseAttempt.objects.create(
        user=user,
        language_slug=language_slug,
        exercise_id=exercise_id,
        user_code=user_code,
        status=status_value,
        response_message=message_value,
        score=score_value,
    )

    return attempt

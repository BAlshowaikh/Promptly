# ----------- IMPORTS ----------
from __future__ import annotations
from typing import Optional
import json
from pathlib import Path

from apps.learning.models import LearningProgress
from apps.accounts.models import User 

# ------------ HELPERS (Private functions) --------------
# ----- HELPER 1: Load the json content ------
def load_learning_content() -> dict:
    """
    Reads and parses the learning content from a local JSON file.

    Returns:
        dict: The full dictionary containing all languages and exercises.
    """
    # Resolve the path of the JSON file
    base_dir = Path(__file__).resolve().parent
    path = base_dir / "learning_content.json"

    # Open and load the json content
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
    
# ----- HELPER 2: Get the language object from the JSON  ------
def get_language(content: dict, language_slug: str) -> dict | None:
    """
    Searches for a specific language dictionary within the loaded content.

    Args:
        content (dict): The full learning content dictionary.
        language_slug (str): The unique string identifier for the language (e.g., 'python').

    Returns:
        dict | None: The language dictionary if found, otherwise None.
    """
    for lang in content.get("languages", []):
        if lang.get("slug") == language_slug:
            return lang
    return None

# ----- HELPER 3: Return full exercise details ------
def get_exercise(language: dict, exercise_id: str) -> dict | None:
    """
    Retrieves a specific exercise from a given language based on its ID.

    Args:
        language (dict): The dictionary representing a specific language.
        exercise_id (str): The unique identifier for the exercise.

    Returns:
        dict | None: The exercise detail dictionary if found, otherwise None.
    """
    for ex in language.get("exercises", []):
        if ex.get("id") == exercise_id:
            return ex
    return None


# ----------- SELECTORS -----------------
# ---- Selector 1: get the learning progress model for a particular language ------
# NOTE: ` * ` is being used to force keyword argument when calling the function
def learning_progress_get(*, user: User, language_slug: str) -> Optional[LearningProgress]:
    """
    Fetches the learning progress record for a specific user and language.
    
    Args:
        user (User): The user instance whose progress is being retrieved.
        language_slug (str): The unique identifier for the programming language.
        
    Returns:
        Optional[LearningProgress]: The progress model instance if it exists, otherwise None.
    """
    return (
        LearningProgress.objects
        .filter(user=user, language_slug=language_slug)
        .first()
    )

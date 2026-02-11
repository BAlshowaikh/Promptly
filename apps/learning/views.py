# ----------- IMPORTS -------------
from django.shortcuts import render
from django.conf import settings
from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication # This will help django chekc the token sengt form react

from core.responses import success_response, error_response

# ------- MODELS ----------
from .models import (
    LearningProgress
)

# --------- HELPERS & SELECTORS -------
from .selectors import (
    load_learning_content,
    get_language,
    get_exercise,
)

# ------ SERIALIZERS --------
from .serializers import (
    LanguageOutSerializer,
    ExerciseListOutSerializer,
    ExerciseDetailOutSerializer,
    ExerciseAttemptOutSerializer,
    SubmitAttemptInSerializer,
    LearningProgressOutSerializer,
)

from apps.learning.services import (
    exercise_submit_attempt
)

# ------------- VIEWS --------------

# --- View 1: Get the list of languages ---
class LanguagesListApi(APIView):
    """
    Endpoint: GET /learn/languages
    
    List all available programming languages.

    Returns:
        A list of language objects containing name, slug, and version.
    """
    
    authentication_classes = [JWTAuthentication]
    
    # Override the get method
    def get(self, request):
        content = load_learning_content()  # Load the content
        languages = content.get("languages", []) # Get the languages object
        
        # Get the list of slugs the user has actually started from the DB
        #  use .values_list for performance to get just the slugs
        started_slugs = []
        if request.user.is_authenticated:
            started_slugs = LearningProgress.objects.filter(
                user=request.user
            ).values_list("language_slug", flat=True)

        # ---------- Logic for started langauges ----------
        # add the 'is_started' key to each dictionary before serializing
        for lang in languages:
            lang["is_started"] = lang["slug"] in started_slugs
        
        # ---------- Logic for percentage_completion ----------
        # Create a dictionary of {slug: percentage} for the user
        user_progress_map = {}
        if request.user.is_authenticated:
            progress_records = LearningProgress.objects.filter(user=request.user)
            user_progress_map = {p.language_slug: p.completion_percentage for p in progress_records}

        for lang in languages:
            slug = lang["slug"]
            lang["is_started"] = slug in user_progress_map
            # Default to 0 if not started
            lang["completion_percentage"] = user_progress_map.get(slug, 0)
            
        # Pass the data to the serializer 
        # `many=True` means I am giving you a list of dictionaries. 
        # loop through them and apply the serializer rules to each one.
        # `.data` will trigger the actual serialization process
        data = LanguageOutSerializer(languages, many=True).data 
        return success_response(
            data=data, 
            message="Successfully retrieved the list of supported languages."
        )
        
# --- View 2: Get the list of exercises for specific langauge---
class LanguageExercisesListApi(APIView):
    """
    Endpoint: GET /learn/languages/{language_slug}/exercises
    
    Retrieve all exercises for a specific language slug.
    """
    
    authentication_classes = [JWTAuthentication]
        
    def get(self, request, language_slug: str):
        content = load_learning_content() # Load the content
        language = get_language(content, language_slug) # Get teh specified language object

        # In case no language was found
        if not language:
            return error_response(
                message=f"Language '{language_slug}' was not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Get the list of excerises dedicated for the specified language
        exercises = language.get("exercises", [])
        
        # Logic to check the progress
        completed_ids = []
        if request.user.is_authenticated:
            progress = LearningProgress.objects.filter(
                user=request.user, 
                language_slug=language_slug
            ).first()
            if progress:
                completed_ids = progress.completed_exercise_ids

        # Apply sequential locking logic (For FE view)
        for index, ex in enumerate(exercises):
            ex_id = str(ex.get("id"))
            ex["is_completed"] = ex_id in completed_ids
            
            if index == 0:
                # First exercise is always unlocked
                ex["is_locked"] = False
            else:
                # Locked if the PREVIOUS exercise wasn't completed
                prev_ex_id = str(exercises[index-1].get("id"))
                ex["is_locked"] = prev_ex_id not in completed_ids
                
        # Return list-only shape (id/title/difficulty)
        data = ExerciseListOutSerializer(exercises, many=True).data # Call the serializer
        
        # Return the list of language's excerises
        return success_response(
            data=data, 
            message=f"Successfully retrieved all exercises for {language_slug.capitalize()}."
        )
        
# --- View 3: Get details for single exercise ---
class ExerciseDetailApi(APIView):
    """
    Endpoint: GET /learn/languages/{language_slug}/exercises/{exercise_id}
    
    Retrieve specific details for a single exercise.
    """
    authentication_classes = []
    
    def get(self, request, language_slug: str, exercise_id: str):
        content = load_learning_content() # Load the content
        language = get_language(content, language_slug) 

        # If no language was found
        if not language:
            return error_response(
                message="Language not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Get the specific exercise details from the JSON
        exercise = get_exercise(language, exercise_id)
        if not exercise:
            return error_response(
                message=f"Exercise with ID '{exercise_id}' does not exist.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Return list-only shape (title, difficulty, prompt, starter_code, hints)
        data = ExerciseDetailOutSerializer(exercise).data
        
        # Specific message for a single object detail
        return success_response(
            data=data, 
            message=f"Exercise '{data.get('title')}' details retrieved successfully."
        )
        
# ----- View 4: Hnadle the submission of an exercise attempt
class SubmitExerciseApi(APIView):
    """
    Endpoint: POST learn/exercise/submit/
    Handles the submission of a user's code attempt for a specific exercise.
    
    This endpoint validates the input, executes the comparison logic via the 
    service layer, and returns the result of the attempt.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    # Override the post function to handle the submit
    def post(self, request):
        """
        Process the exercise submission.
        """
        
        # Validate the incoming JSON payload using the serializer
        serializer = SubmitAttemptInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True) # Validate any custom or field level checks

        # Extract the cleaned and validated data, ready to be passed to the Service layer
        data = serializer.validated_data

        # Extract user (Currently uses AnonymousUser until Auth is implemented)
        user = request.user

        try:
            # Call the service with passed parameters
            attempt = exercise_submit_attempt(
                user=user,
                language_slug=data["language_slug"],
                exercise_id=data["exercise_id"],
                user_code=data["user_code"],
            )
            
        except ValueError as exc:
            msg = str(exc)

            if "not found" in msg.lower():
                return error_response(
                    message=msg,
                    status_code=status.HTTP_404_NOT_FOUND
                )

            # Fallback for other potential ValueErrors (400 Bad Request)
            return error_response(
                message=msg,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        #Transform the resulting Model instance back into JSON via the Output Serializer
        out_data = ExerciseAttemptOutSerializer(attempt).data
        return success_response(
            data=out_data, 
            message=f"Attempt processed: {out_data['status'].upper()}"
        )

# ----- View 5: Retrieve a list of learning progress per language records for the user
class LearningProgressListApi(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Endpoint: GET /learn/progress
        Returns progress for all languages for the current user.
        """
        try:
            # Extract user (Currently uses AnonymousUser until Auth is implemented)
            user = request.user  

            # Query the database for all progress records belonging to the user
            qs = (
                LearningProgress.objects
                .filter(user=user)
                .order_by("language_slug")
            )

            # Serialize the QuerySet into a list of dictionaries
            data = LearningProgressOutSerializer(qs, many=True).data

            return success_response(
                data=data,
                message="Successfully retrieved learning progress."
            )

        except Exception as exc:
            return error_response(
                message=str(exc),
                status_code=500
            )
            
    def post(self, request):
        """
        Endpoint: POST /learn/progress/
        Payload: {"language_slug": "python"}
        """
        language_slug = request.data.get("language_slug")
        
        if not language_slug:
            return error_response(message="language_slug is required", status_code=400)
        
        user = request.user
        if not user.is_authenticated:
            User = get_user_model()
            user = User.objects.filter(is_superuser=True).first()
 
        # This prevents duplicate records if a user clicks "Start" twice.
        progress, created = LearningProgress.objects.get_or_create(
            # user=request.user if request.user.is_authenticated else None, # Handle null user for now
            user=user,
            language_slug=language_slug,
            defaults={
                "current_exercise_id": "", 
                "completed_exercise_ids": []
            }
        )

        message = "Path started successfully." if created else "Path already in progress."
        data = LearningProgressOutSerializer(progress).data
        
        return success_response(data=data, message=message) 
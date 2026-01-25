# ------------- IMPORTS --------------
from rest_framework import serializers

# ------ Serializer 1: List the languages ---------
class LanguageOutSerializer(serializers.Serializer):
    """
    Represents the public-facing data for a programming language.
    """
    slug = serializers.CharField()
    name = serializers.CharField()
    version = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)

# --------- Serializer 2: List Exercises for each language -----
class ExerciseListOutSerializer(serializers.Serializer):
    """
    Summary data for an Exercise, optimized for collection endpoints.
    
    Excludes heavy fields like 'prompt' or 'starter_code' to keep 
    list responses lightweight and performant.
    """
    id = serializers.CharField()
    title = serializers.CharField()
    difficulty = serializers.CharField()

# ------ Serializer 3: Details for each exercise -----------
class ExerciseDetailOutSerializer(serializers.Serializer):
    """
    Comprehensive data for a single Exercise instance.
    
    Includes all necessary fields for a user to begin solving a challenge,
    including technical requirements and instructional hints.
    """
    id = serializers.CharField()
    title = serializers.CharField()
    difficulty = serializers.CharField()
    prompt = serializers.CharField()
    starter_code = serializers.CharField()
    hints = serializers.ListField(child=serializers.CharField(), min_length=2, max_length=2)
    
# ------ Serializer 4: Excercise submission Input Serializer -----------
class SubmitAttemptInSerializer(serializers.Serializer):
    """
    Validates the incoming payload for an exercise submission.

    Args:
        language_slug (str): The slug of the programming language used.
        exercise_id (str): The unique identifier of the exercise being attempted.
        user_code (str): The source code submitted by the user.
    """
    language_slug = serializers.CharField()
    exercise_id = serializers.CharField()
    user_code = serializers.CharField()

# ------ Serializer 5: Exercise Attempt Output Serializer -----------
class ExerciseAttemptOutSerializer(serializers.Serializer):
    """
    Represents the result and metadata of an exercise attempt.

    Used to return the outcome of a submission, including the evaluation
    status, feedback message, and the time the attempt was logged.
    """
    id = serializers.IntegerField()
    language_slug = serializers.CharField()
    exercise_id = serializers.CharField()
    user_code = serializers.CharField()
    status = serializers.CharField()
    response_message = serializers.CharField(allow_blank=True)
    score = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    created_at = serializers.DateTimeField()

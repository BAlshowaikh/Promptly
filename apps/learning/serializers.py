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
    
# ------ Serializer 4:  -----------

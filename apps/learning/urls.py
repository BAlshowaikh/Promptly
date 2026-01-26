# ---------- IMPORTS --------------
from django.urls import path

# -------- VIEWS --------
from .views import (
    LanguagesListApi, 
    LanguageExercisesListApi, 
    ExerciseDetailApi,
    SubmitExerciseApi,
    LearningProgressListApi
)

app_name = "learning"

urlpatterns = [
    # GET: Shows minimal data about language 
    path("learn/languages", 
         LanguagesListApi.as_view(), 
         name="languages-list"),
    
    # GET: Shows list of exercises dedicated to a language
    path("learn/languages/<str:language_slug>/exercises", 
         LanguageExercisesListApi.as_view(), 
         name="exercises-list"),
    
    # GET: Shows details for specific excerise in specific language
    path("learn/languages/<str:language_slug>/exercises/<str:exercise_id>",
        ExerciseDetailApi.as_view(),
        name="exercise-detail",
    ),
    
    # POST: Handles the submission of exercises
    path("learn/exercise/submit/", 
         SubmitExerciseApi.as_view(), 
         name="exercise-submit"
    ),
    
    # GET: Retrieve the learning progress for logged in user
    path("learn/progress/",
         LearningProgressListApi.as_view(),
         name="learning-progress-list"
    ),
]

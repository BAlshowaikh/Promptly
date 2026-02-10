
from django.contrib import admin
from .models import (
    LearningProgress,
    ExerciseAttempt,
)

# Register your models here.
admin.site.register(LearningProgress)
admin.site.register(ExerciseAttempt)

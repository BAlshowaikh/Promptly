from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import TimeStampedModel


class AttemptStatus(models.TextChoices):
    PASSED = "passed", "Passed"
    FAILED = "failed", "Failed"
    ERROR = "error", "Error"

# --------- Model 1: To track progress per user per language/path
class LearningProgress(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="learning_progress")
    language_slug = models.CharField(max_length=50)

    started_at = models.DateTimeField(default=timezone.now)
    last_activity_at = models.DateTimeField(default=timezone.now)

    # These will be retrived from the JSON file (Probably updated via signals)
    current_exercise_id = models.CharField(max_length=50, blank=True, default="")
    completed_exercise_ids = models.JSONField(default=list, blank=True)

    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        db_table = "learning_progress"
        indexes = [
            models.Index(fields=["user", "language_slug"]),
            models.Index(fields=["language_slug"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["user", "language_slug"], name="uq_learning_progress_user_language"),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.language_slug}"


# ---------- Model 2: To store each user attempt/submission for a specific exercise
class ExerciseAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="exercise_attempts")
    language_slug = models.CharField(max_length=50)

    # These will be retrived from the JSON file
    exercise_id = models.CharField(max_length=50)
    
    user_code = models.TextField()

    status = models.CharField(max_length=10, choices=AttemptStatus.choices)
    # This is the customized message
    response_message = models.TextField(blank=True, default="")
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "exercise_attempt"
        indexes = [
            models.Index(fields=["user", "language_slug", "created_at"]),
            models.Index(fields=["exercise_id"]),
            models.Index(fields=["status"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id}:{self.exercise_id}:{self.status}"

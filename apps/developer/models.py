from django.conf import settings
from django.db import models
from django.forms import ValidationError
from django.utils import timezone

from apps.ai_models.models import AiModel
from core.models import TimeStampedModel

# An ENUM for ddl to assign the role of the chosen models for that particular session
class SessionRole(models.TextChoices):
    CODER = "coder", "Coder"
    EXPLAINER = "explainer", "Explainer"

# An ENUM to decide the respond mode for a particular session 
class RunMode(models.TextChoices):
    PARALLEL = "parallel", "Parallel"
    PIPELINE = "pipeline", "Pipeline"

# An ENUM to track the responde result when user clicks "Run" button
class RunResultStatus(models.TextChoices):
    SUCCESS = "success", "Success"
    ERROR = "error", "Error"
    TIMEOUT = "timeout", "Timeout"
    CANCELLED = "cancelled", "Cancelled"

# ------- Model 1: A session represnts "project" or "chat", user can create many sessions with different configurations
class DevSession(TimeStampedModel):
    """
    Represents a unified workspace or 'project' created by a user.
    A session acts as a container for specific AI orchestration tasks, 
    grouping together model configurations and execution history.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="dev_sessions")
    title = models.CharField(max_length=200)
    run_mode = models.CharField(max_length=20, choices=RunMode.choices, default=RunMode.PIPELINE)
    is_archived = models.BooleanField(default=False)

    last_activity_at = models.DateTimeField(default=timezone.now)
    
    # Add a validation to ckeck if the user has more than 5 sessions before creating anew one
    def clean(self):
        # 1. Count how many active (non-archived) sessions the user has
        session_count = DevSession.objects.filter(
            user=self.user, 
            is_archived=False
        ).count()

        # 2. If they hit the limit, raise an error
        if not self.pk and session_count >= 5:
            raise ValidationError("You have reached the maximum limit of 5 active sessions.")

    def save(self, *args, **kwargs):
        self.full_clean() # This triggers the clean() method before saving
        super().save(*args, **kwargs)

    class Meta:
        db_table = "dev_session"
        indexes = [
            models.Index(fields=["user", "is_archived"]),
            models.Index(fields=["last_activity_at"]),
            models.Index(fields=["run_mode"]),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.title}"


# ------- Model 2: A model to store each session's configurations 
class DevSessionModelConfig(TimeStampedModel):
    """
    Stores the specific configuration for an AI model within a session.
    This defines 'who' the model is (e.g., GPT-4), its 'role' (Coder or Explainer), 
    and 'how' it should behave (temperature, system prompts).
    """
    session = models.ForeignKey(DevSession, on_delete=models.CASCADE, related_name="model_configs")
    ai_model = models.ForeignKey(AiModel, on_delete=models.PROTECT, related_name="session_configs")

    role = models.CharField(max_length=20, choices=SessionRole.choices)
    temperature = models.DecimalField(max_digits=3, decimal_places=2, default=0.70)

    # Optional prompt that user can send to the model 
    system_prompt = models.TextField(blank=True, default="")
    is_enabled = models.BooleanField(default=True)

    class Meta:
        db_table = "dev_session_model_config"
        indexes = [
            models.Index(fields=["session", "role", "is_enabled"]),
            models.Index(fields=["ai_model"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "ai_model", "role"],
                name="uq_dev_session_model_config_session_model_role",
            ),
        ]

    def __str__(self):
        return f"{self.session_id}:{self.ai_model_id}:{self.role}"


# --------- Model 3: When user clicks the Run button
class DevRun(models.Model):
    """
    Represents a single execution event within a session.
    Whenever a user clicks 'Run', this model captures the input (prompt + code)   
    """
    session = models.ForeignKey(DevSession, on_delete=models.CASCADE, related_name="runs")

    user_prompt = models.TextField()
    context_code = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "dev_run"
        indexes = [
            models.Index(fields=["session", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.session_id}:{self.created_at.isoformat()}"


class DevRunResult(models.Model):
    """
    Captures the specific output and performance data from a single AI model 
    during a DevRun. It stores the model's response alongside critical 
    metrics like latency and token usage for side-by-side comparison.
    """
    run = models.ForeignKey(DevRun, on_delete=models.CASCADE, related_name="results")
    session_model_config = models.ForeignKey(
        DevSessionModelConfig, on_delete=models.PROTECT, related_name="run_results"
    )

    output = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=RunResultStatus.choices)

    response_message = models.TextField(blank=True, default="")

    latency_ms = models.PositiveIntegerField(null=True, blank=True)
    tokens_in = models.PositiveIntegerField(null=True, blank=True)
    tokens_out = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "dev_run_result"
        indexes = [
            models.Index(fields=["run", "created_at"]),
            models.Index(fields=["status"]),
        ]
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.run_id}:{self.session_model_config_id}:{self.status}"

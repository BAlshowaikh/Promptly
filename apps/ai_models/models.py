# --------- Imports --------------
from django.db import models
from core.models import TimeStampedModel

# Define the enums using TextChoices to create a drop down menu
class AiProvider(models.TextChoices):
    OPENAI = "openai", "OpenAI"
    GOOGLE = "google", "Google"
    LOCAL = "local", "Local"

# ----------- Model 1: This model will store the LLMs 
class AiModel(TimeStampedModel):
    provider = models.CharField(max_length=32, choices=AiProvider.choices)
    model_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "ai_model"
        indexes = [
            models.Index(fields=["provider", "is_active"]),
            models.Index(fields=["model_name"]),
        ]
        # Prevents adding the same llm for the same provider
        constraints = [
            models.UniqueConstraint(fields=["provider", "model_name"], name="uq_ai_model_provider_name"),
        ]

    def __str__(self):
        return f"{self.provider}:{self.model_name}"

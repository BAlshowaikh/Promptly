from django.db import models


# This model will be used in each created db model 
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Means don't create a new db table for this class, 
        # just add this class's fields whenever it's been called in other models
        abstract = True

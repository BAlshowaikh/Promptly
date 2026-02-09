
from django.contrib import admin
from .models import ( 
    DevSession, 
    DevRunResult,
    DevRun,
    DevSessionModelConfig
)


admin.site.register(DevSession)
admin.site.register(DevRunResult)
admin.site.register(DevRun)
admin.site.register(DevSessionModelConfig)

from rest_framework import serializers
from apps.ai_models.models import AiModel
from .models import (
    DevRunResult,
    DevSession, 
    DevSessionModelConfig, 
    DevRun, 
    RunResultStatus, 
    SessionRole, 
    RunMode
)

# ---------- Serializer 1: To show the list of the avaiable AI models
class AiModelOutSerializer(serializers.ModelSerializer):
    """
    Public-facing data for available AI models (Llama, GPT-4, etc.)
    """
    class Meta:
        model = AiModel
        fields = ['id', 'provider', 'model_name']
        
# -------------- Serializer 2: Handles the listing/adding and updating for the llms setting in each session
class DevSessionModelConfigSerializer(serializers.ModelSerializer):
    """
    Handles both Input (creating/updating) and Output (viewing) 
    for Coder and Explainer settings per session.
    """
    # For Output: Show the details of the linked AI model
    ai_model_details = AiModelOutSerializer(source='ai_model', read_only=True)
    
    class Meta:
        model = DevSessionModelConfig
        fields = [
            'id', 'ai_model', 'ai_model_details', 
            'role', 'temperature', 'system_prompt', 'is_enabled'
        ]
        # ai_model is used for input (ID), ai_model_details for output (JSON)
        extra_kwargs = {'ai_model': {'write_only': True}}
        
# ------- Serializer 3: Listing for user sessions (chats)
class DevSessionOutSerializer(serializers.ModelSerializer):
    """
    Represents the public-facing data for a developer session.
    Used for listing sessions in a sidebar or dashboard.
    """
    class Meta:
        model = DevSession
        fields = [
            'id',
            'title',
            'run_mode',
            'is_archived',
            'last_activity_at'
        ]


# ---------- Serializer 4: Handles the creation of 
class DevSessionCreateInSerializer(serializers.ModelSerializer):
    """
    Handles the creation of a new session. 
    """
    class Meta:
        model = DevSession
        fields = ['title', 'run_mode']
        
# ----------- Serializer 5: To handle creation of DevSession and DevSessionModelConfiguration
class DevSessionCreateAllInSerializer(serializers.ModelSerializer):
    """
    Serializer to handle the creation of a Dev session and its associated LLMs 
    """
    # Expect and array of 2 config objects from the frontend
    model_configs = DevSessionModelConfigSerializer(many=True)

    class Meta:
        model = DevSession
        fields = ['title', 'run_mode', 'model_configs']

    def create(self, validated_data):
        configs_data = validated_data.pop('model_configs')
        # 1. Create the session
        session = DevSession.objects.create(**validated_data)
        
        # 2. Create the associated model configurations
        for config in configs_data:
            DevSessionModelConfig.objects.create(session=session, **config)
            
        return session
    
# ----------- Serialzier 6: Toi get the list of the ai models avaibale
class AiModelOutSerializer(serializers.ModelSerializer):
    """
    Data for the AI Model dropdown menu in the session creation.
    """
    # Combines provider and model name for a cleaner UI label
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = AiModel
        fields = ['id', 'display_name', 'provider', 'model_name']

    def get_display_name(self, obj):
        return f"{obj.get_provider_display()} - {obj.model_name}"
    
    
# ---------- Serializer 7: Chat Result (Individual AI Responses)
class DevRunResultOutSerializer(serializers.ModelSerializer):
    # This reaches into the config to pull the role (coder/explainer)
    role = serializers.CharField(source='session_model_config.role')

    class Meta:
        model = DevRunResult
        fields = ['id', 'role', 'output', 'status', 'created_at']

# ---------- Serializer 8: Chat Run (The User Prompt Grouping)
class DevRunOutSerializer(serializers.ModelSerializer):
    # 'results' matches the related_name in your DevRunResult model
    results = DevRunResultOutSerializer(many=True, read_only=True)

    class Meta:
        model = DevRun
        fields = ['id', "initiator_role", 'user_prompt', 'context_code', 'status', 'created_at', 'results']
        
# ------- Serializer 9: Deatailed serializer for user session
class DevSessionDetailOutSerializer(serializers.ModelSerializer):
    """
    Comprehensive data for a single Session, including its
    Coder and Explainer configurations and their history
    """
    # This will retrun two objects one for the coder and the other for explainer
    model_configs = DevSessionModelConfigSerializer(many=True, read_only=True)
    
    runs = serializers.SerializerMethodField()
    
    class Meta:
        model = DevSession
        fields = [
            'id', 
            'title', 
            'run_mode', 
            'is_archived', 
            'last_activity_at', 
            'model_configs',
            'runs'
        ]
        
    def get_runs(self, obj):
        # 1. Newest 5 runs
        last_five_runs = obj.runs.all().order_by('-created_at')[:5]
        
        # 2. Flip them so the oldest of the 5 is first (standard chat flow)
        ordered_runs = list(reversed(last_five_runs))
        
        # 3. Use your nested serializer
        return DevRunOutSerializer(ordered_runs, many=True).data
    
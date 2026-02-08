import json
import logging
from ai_models.services import OllamaOrchestrator
from apps.developer.models import DevRunResult, RunResultStatus

logger = logging.getLogger(__name__)

def generate_dev_mode_stream(session, user_prompt, history_messages, run_instance):
    """
    Yields JSON chunks sequentially: Coder first, then Explainer.
    """
    try:
        # 1. Get configs from the session
        coder_cfg = session.model_configs.get(role="coder", is_enabled=True)
        explainer_cfg = session.model_configs.get(role="explainer", is_enabled=True)
        
        # Initilizee an instance of the LLMs and pass the session config for each model
        orchestrator = OllamaOrchestrator(coder_cfg, explainer_cfg)
        
        full_code = "" # Catch what the coder responded with so this will be passed to the explainer
        # --- PHASE A: CODER ---
        # Catch every word the coder writres
        try:
            for chunk in orchestrator.get_coder_stream(user_prompt, history_messages):
                content = chunk.content
                full_code += content # update the bucket
                # Wrap in JSON so the frontend knows who is talking
                # 'yeild': sends a piece of data out immediately and then waits to send the next one
                yield json.dumps({"sender": "coder", "text": content}) + "\n"

            # --- SAVE CODER RESULT ---
            DevRunResult.objects.create(
                run=run_instance,
                session_model_config=coder_cfg,
                output=full_code,
                status=RunResultStatus.SUCCESS
            )
        except Exception as e:
            logger.error(f"Coder Stream Error: {e}")
            yield json.dumps({"sender": "coder", "error": "Coder failed to respond. Check Ollama status."}) + "\n"
            return # Stop if the primary coder fails
    
    # --- PHASE B: EXPLAINER ---
    full_explanation = ""
    try:
        # Triggered automatically once Coder's loop finishes
        for chunk in orchestrator.get_explainer_stream(user_prompt, full_code, history_messages):
            content = chunk.content
            full_explanation += content
            yield json.dumps({"sender": "explainer", "text": content}) + "\n"
            
        # --- SAVE EXPLAINER RESULT ---
        DevRunResult.objects.create(
            run=run_instance,
            session_model_config=explainer_cfg,
            output=full_explanation,
            status=RunResultStatus.SUCCESS
        )
    except Exception as e:
        logger.critical(f"Orchestrator Setup Error: {e}")
        yield json.dumps({"sender": "system", "error": "System configuration error."}) + "\n"
    

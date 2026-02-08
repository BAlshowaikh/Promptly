import json
import logging
from langchain_core.messages import HumanMessage, AIMessage

from ai_models.services import OllamaOrchestrator
from apps.developer.models import DevRunResult, RunResultStatus

logger = logging.getLogger(__name__)

# -------------- Function 1: Handle the calling for the agents and send the data (in chuncks) to the FE
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
            for chunk in orchestrator.get_coder_stream(user_prompt, history_messages['coder']):
                content = chunk.content
                full_code += content # update the bucket
                # Wrap in JSON so the frontend knows who is talking
                # 'yield': sends a piece of data out immediately and then waits to send the next one
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
            for chunk in orchestrator.get_explainer_stream(user_prompt, full_code, history_messages['explainer']):
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
            
            # Update the db field for each run
            run_instance.status = RunResultStatus.SUCCESS
            run_instance.save()
            
        except Exception as e:
                logger.error(f"Explainer Stream Error: {e}")
                yield json.dumps({"sender": "explainer", "error": "Code generated, but explanation failed."}) + "\n"
            
    except Exception as e:
        logger.critical(f"Orchestrator Setup Error: {e}")
        run_instance.status = RunResultStatus.ERROR
        run_instance.save()
        yield json.dumps({"sender": "system", "error": "System configuration error."}) + "\n"
    

# ---------------- Function 2: Retrieve the last 5 successful messages from the DB to show them  in the chat
def get_session_history(run_instance, k=5):
    """
    Fetches the last k successful runs from the same session 
    to provide conversational memory for Coder chat and Explainer Chat.
    """
    coder_history = []
    explainer_history = []
    
    # Get previous successful runs in this session
    previous_runs = run_instance.session.runs.filter(
        status=RunResultStatus.SUCCESS
    ).exclude(id=run_instance.id).order_by('-created_at')[:k]

    for run in reversed(previous_runs):
        user_msg = HumanMessage(content=run.user_prompt)
        
        # --- Coder's View of the Past ---
        coder_res = run.results.filter(session_model_config__role="coder").first()
        if coder_res:
            coder_history.append(user_msg)
            coder_history.append(AIMessage(content=coder_res.output))
            
        # --- Explainer's View of the Past ---
        explainer_res = run.results.filter(session_model_config__role="explainer").first()
        if explainer_res:
            # We also give the Explainer the user prompt for context
            explainer_history.append(user_msg) 
            explainer_history.append(AIMessage(content=explainer_res.output))
            
    return {"coder": coder_history, "explainer": explainer_history}
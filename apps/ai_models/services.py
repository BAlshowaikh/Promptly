"""
   This file will be the main service for Ollama LLMs 
"""
import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.memory import ConversationBufferWindowMemory # Reacts as a short-term memory for AI so we can show the last messages

load_dotenv()

class OllamaOrchestrator:
    """
    This class will hold the initilization of two distinct LLM instances.
    """
    
    def __init__(self, coder_config, explainer_config):
        """
        Initilization for ollama LLMs.
        """
        
        # ---- 1.Setup for Coder Model using the passed configurations (Our model)
        self.coder_llm = ChatOllama(
            model = coder_config.ai_model.model_name,
            temperature=float(coder_config.temperature),
            base_url=os.getenv("OLLAMA_URL")
        )
        
        # Defines the SystemMessage to be passed to the LLM
        self.coder_system_prompt = coder_config.system_prompt or "You are an expert coder. Output only code."
        
        # ----- 2. Setup for explainer using the passed configurations (Our model)
        self.explainer_llm = ChatOllama(
            model = explainer_config.ai_model.model_name,
            temperature=float(explainer_config.temperature),
            base_url=os.getenv("OLLAMA_URL")
        )
         # Defines the SystemMessage to be passed to the LLM
        self.explainer_system_prompt = explainer_config.system_prompt or "You are a technical tutor. Explain code clearly."
        
        # ------ Memory config
        # Remember the last 5 intercation
        self.memory = ConversationBufferWindowMemory(k=5, return_messages=True)
        
        # ---- Function 1:
    def get_coder_stream(self, user_prompt, history_messages):
        """
        Creates a stream for the Coder.
        history_messages: list of previous Human/AI messages
        """
        
        # Send the system message first in every request
        messages = [SystemMessage(content=self.coder_system_prompt)]
        # pastes in the previous back-and-forth so the AI knows what was discussed earlier
        messages.extend(history_messages)
        # adds the new current task
        messages.append(HumanMessage(content=user_prompt))
        
        # .stream() because we want to receive the LLM responds in the same time rather tan waiting for the whole message to finish
        # Basically it chuncks the LLM respond and sends it 
        return self.coder_llm.stream(messages)

        
    def get_explainer_stream(self, user_prompt, coder_output, history_messages):
        """
        Creates a stream for the Explainer.
        """
            
        combined_prompt = (
            f"The developer asked about '{user_prompt}'\n"
            f"The coder agent responded to developer with this code:\n {coder_output}\n"
            f"You have to be the explainer and expalin the code to the user."
        )
            
        messages = [SystemMessage(content=self.explainer_system_prompt)]
        messages.extend(history_messages)
        messages.append(HumanMessage(content=combined_prompt))

            return self.explainer_llm.stream(messages)
        
import os
from dotenv import load_dotenv
from langchain_ollama.llms import OllamaLLM
from langchain_groq import ChatGroq
import requests

load_dotenv("app.config")
load_dotenv()

def get_model(use_api=False):
    try:
        if use_api:
            model_name = os.getenv("LLM_MODEL_API")
            api_key = os.getenv("GROQ_API_KEY")
            return ChatGroq(model=model_name, api_key=api_key)
        else:
            model_name = os.getenv("LLM_MODEL_LOCAL")
            return OllamaLLM(model=model_name)
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Ollama isn't running!!")
    except Exception as e:
        raise RuntimeError(f"Failed to initialize model: {e}")

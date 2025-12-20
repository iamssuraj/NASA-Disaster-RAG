import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv("app.config")
load_dotenv()


def getPrompt(filename):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(current_dir, "..", "data", "prompts", filename)
        with open(prompt_path, "r") as f:
            return f.read()
    except Exception as e:
        raise RuntimeError(f"Failed to load prompt '{filename}': {e}")

def getSystemPrompt():
    try:
        prompt_path = os.getenv("SYSTEM_PROMPT")
        with open(prompt_path) as f:
            return f.read()
    except Exception as e:
        raise RuntimeError(f"Failed to load system prompt: {e}")

def getSamplePrompts():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sample_prompts_path = os.path.join(current_dir, "..", "data", "prompts", "samplePrompts.txt")
        
        with open(sample_prompts_path) as f:
            prompts = [line.strip() for line in f.readlines() if line.strip()]
        return prompts
    except Exception as e:
        return [e]

def writeLog(message, log_file="app.log"):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [INFO] {message}"
        
        with open(log_file, "a") as f:
            f.write(log_entry + "\n")
    except Exception as e:
        print(f"Error writing to log: {e}")

def getFooterHtml():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        footer_path = os.path.join(current_dir, "..", "data", "footer.html")
        with open(footer_path, "r") as f:
            return f.read()
    except Exception as e:
        raise RuntimeError(f"Failed to load footer: {e}")


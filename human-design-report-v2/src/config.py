from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "output")
PROMPTS_DIR = BASE_DIR / "prompts"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
TEMPLATES_DIR = BASE_DIR / "templates"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
REPORT_LANGUAGE = os.getenv("REPORT_LANGUAGE", "en")
TEMPERATURE = 0.2

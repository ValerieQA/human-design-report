from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, TEMPERATURE


class OpenAIClient:
    def __init__(self) -> None:
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is missing in environment.")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL

    def complete(self, prompt: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            temperature=TEMPERATURE,
            input=prompt,
        )
        return response.output_text.strip()

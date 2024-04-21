from abc import abstractmethod
import os
from openai import OpenAI
from dotenv import load_dotenv


class llmAPI:
    @abstractmethod
    def make_request(self, prompt):
        raise NotImplementedError


class gpt4Llm(llmAPI):
    def __init__(self) -> None:
        load_dotenv()
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = OpenAI(
			api_key=self.api_key,
		)

    def make_request(self, prompt: str, persona: str = None, model: str = "gpt-3.5-turbo"):
        completion = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": persona},
                {"role": "user", "content": prompt}
            ]
        )
        print(completion.choices[0].message)
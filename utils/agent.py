import os
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic import BaseModel, Field

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class ResponseModel(BaseModel):
    product: str = Field(...,
                         description="The main item or object the user is referring to.")
    intent: str = Field(
        None, description="The qualifier, description, or attribute that shows what kind, type, or preference the user has about the product (e.g., size, color, brand, or quantity).")


model = GeminiModel(
    'gemini-2.0-flash-exp', provider=GoogleGLAProvider(api_key=GEMINI_API_KEY)
)
agent = Agent(model, output_type=ResponseModel)
agent.system_prompt = """You are an intelligent text processing agent. Your task is to extract information according to the given schema"""

query = input("Search: ")

result = agent.run_sync(query, model_settings={
    "temperature": 0.2,
})

print(result.output)

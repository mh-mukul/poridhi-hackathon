import os
from pydantic_ai import Agent
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from configs.logger import logger

load_dotenv()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
OLLAMA_URL = os.getenv("OLLAMA_URL")


class ResponseModel(BaseModel):
    sorted_index: list = Field(
        ..., description="The list of products index sorted in ascending order by users preference",)


ollama_model = OpenAIModel(
    model_name=OLLAMA_MODEL, provider=OpenAIProvider(
        base_url=OLLAMA_URL, api_key="apikey")
)

agent = Agent(ollama_model, output_type=ResponseModel)


def run_agent(query: str, products: list):

    agent.system_prompt = f"""You are a helpful assistant. You will be given a list of products and a user prefered item. Your task is to sort the list of products based on the user's preference. And return the sorted list of products index in ascending order. Here is the list of products: {products}."""

    user_prompt = f"""The user prefered item is {query}. Please return the sorted list of products index in ascending order. Do not include any other text in your response."""
    try:
        result = agent.run_sync(user_prompt, model_settings={
            "temperature": 0.2,
        })
        logger.info(f"Agent result: {result}")
        if result.output is None:
            logger.error("No output from the agent.")
            return None
        return result.output
    except Exception as e:
        logger.error(f"Error extracting intend: {e}")
        return None

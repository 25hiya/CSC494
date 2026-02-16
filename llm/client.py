# llm/client.py

from langchain_ollama import ChatOllama
from config import LLM_MODEL, TEMPERATURE, MAX_TOKENS


def get_llm():
    return ChatOllama(
        model=LLM_MODEL,          # llama3:8b
        temperature=TEMPERATURE,
        num_predict=MAX_TOKENS,
    )

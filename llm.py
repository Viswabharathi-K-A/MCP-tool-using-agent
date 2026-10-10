import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

llm = ChatOpenAI(
    model="gpt-5",
    api_key=os.getenv("OPENAI_API_KEY")
)
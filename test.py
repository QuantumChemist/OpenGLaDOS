import os
import re
from dotenv import load_dotenv
import textwrap
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage

# Load environment variables
load_dotenv()
os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.environ.get('HF_TOKEN')

# Initialize the HuggingFace LLM endpoint
llm = HuggingFaceEndpoint(repo_id="mistralai/Mistral-7B-Instruct-v0.2", temperature=0.3)

# Store for maintaining session history
store = {}


# Function to wrap text for better readability
def wrap_text(text, width=110):
    return textwrap.fill(text, width=width)


# Function to get or create session history
def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


# Initialize conversation handling
convo = RunnableWithMessageHistory(runnable=llm, get_session_history=get_session_history)

# Main conversation loop
while True:
    prompt = input('How can I help you?\n\n')
    if prompt.lower() == "quit":
        break

    # Invoke the model with the user's prompt
    try:
        answer = convo.invoke(
            HumanMessage(prompt),
            config={"configurable": {"session_id": "1"}},
        )
        print("\n")
        print(wrap_text(answer))
    except Exception as e:
        print(f"An error occurred: {e}")

    print('\n')

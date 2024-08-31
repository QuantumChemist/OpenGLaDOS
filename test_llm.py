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
llm = HuggingFaceEndpoint(repo_id="mistralai/Mistral-7B-Instruct-v0.2", temperature=0.2)

# Store for maintaining session history
store = {}


# Function to wrap text for better readability
def wrap_text(text, width=110):
    lines = text.split('\n')
    wrapped_lines = [textwrap.fill(line, width=width) for line in lines]
    wrapped_text = '\n'.join(wrapped_lines)
    return wrapped_text


# Function to get or create session history
def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


# Initialize conversation handling
convo = RunnableWithMessageHistory(runnable=llm, get_session_history=get_session_history)

# Main conversation loop
prompt = input('How can I help you?\n\n')
while prompt.lower() != "quit":
    # Invoke the model with the user's prompt
    answer = convo.invoke(
        HumanMessage(prompt),
        config={"configurable": {"session_id": "1"}},
    )
    # Print the wrapped response
    print("\n")
    print(wrap_text(answer))

    # Prompt for the next input
    prompt = input('\nHow can I help you further?\n\n')
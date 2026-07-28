import os
import sys
from dotenv import load_dotenv
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver

def clean_content(content):
    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
            else:
                text_parts.append(str(block))
        return "".join(text_parts)
    return str(content)

def main():
    # 1. Load environment variables from .env file
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path=dotenv_path)

    # Validate API keys exist
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY not found in .env file.", file=sys.stderr)
        sys.exit(1)
    if not os.getenv("SERPER_API_KEY"):
        print("Error: SERPER_API_KEY not found in .env file.", file=sys.stderr)
        sys.exit(1)

    print("Initializing Search Tool...")
    search = GoogleSerperAPIWrapper()

    print("Initializing Gemini Model (gemini-3.5-flash-lite)...")
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        api_key=os.getenv("GOOGLE_API_KEY")
    )

    print("Creating Agent with Memory checkpointer...")
    # Initialize MemorySaver checkpointer
    memory = MemorySaver()

    # create_agent compiles a LangGraph agent that automatically executes tool calling
    agent = create_agent(
        model=llm,
        tools=[search.run],
        system_prompt=(
            "You are a helpful chatbot assistant. "
            "You have access to a Google Search tool to answer real-time questions "
            "and factual information about current events. Always search if you need "
            "up-to-date facts (e.g. weather, news, current prices)."
        ),
        checkpointer=memory
    )

    print("\n" + "="*50)
    print("Chatbot Initialized! Type 'exit' or 'quit' to end the session.")
    print("="*50 + "\n")

    # LangGraph Thread configuration for session memory persistence
    config = {"configurable": {"thread_id": "Prathamesh"}}

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "q"]:
                print("\nGoodbye!")
                break

            print("Thinking...", end="\r")
            # Invoke agent with only the new message. MemorySaver handles history retrieval automatically.
            response = agent.invoke(
                {"messages": [{"role": "user", "content": user_input}]},
                config
            )
            
            # Print the final response from the agent
            final_reply = clean_content(response["messages"][-1].content)
            print(f"Agent: {final_reply}\n")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}\n")

if __name__ == "__main__":
    main()

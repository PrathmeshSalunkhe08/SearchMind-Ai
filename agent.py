import os
import sys
import math
import requests
import arxiv
from dotenv import load_dotenv
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver

# --- TOOLS DEFINITION ---
@tool
def calculator(expression: str) -> str:
    """Calculates the result of a mathematical expression.
    Input should be a valid mathematical expression string (e.g. '2 + 2', '15 * 8', '100 / 4', '2**10', 'sqrt(144)').
    """
    try:
        allowed_names = {
            'abs': abs, 'round': round, 'pow': pow, 'min': min, 'max': max,
            'sqrt': math.sqrt, 'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
            'log': math.log, 'pi': math.pi, 'e': math.e
        }
        result = eval(expression, {'__builtins__': None}, allowed_names)
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"

@tool
def arxiv_search(query: str) -> str:
    """Searches scientific research papers on arXiv.
    Input should be a search query topic or research domain (e.g. 'quantum computing', 'transformer models', 'artificial intelligence').
    Returns paper titles, authors, published dates, category, formatted abstract summary, and direct PDF download links.
    """
    try:
        client = arxiv.Client()
        search = arxiv.Search(query=query, max_results=3, sort_by=arxiv.SortCriterion.Relevance)
        results = list(client.results(search))
        if not results:
            return 'No research papers found for the query.'
        output = []
        for i, paper in enumerate(results, 1):
            author_names = [a.name for a in paper.authors[:3]]
            authors_str = ', '.join(author_names)
            if len(paper.authors) > 3:
                authors_str += ' et al.'
            clean_summary = ' '.join(paper.summary.replace('\n', ' ').split())
            if len(clean_summary) > 350:
                clean_summary = clean_summary[:350] + '...'
            pub_date = paper.published.strftime('%B %d, %Y')
            category = getattr(paper, 'primary_category', 'Research')
            paper_id = paper.entry_id.split('/')[-1]

            formatted_paper = (
                f"### 📄 {i}. {paper.title.strip()}\n"
                f"- **👥 Authors:** {authors_str}\n"
                f"- **📅 Published:** {pub_date} | **🏷️ Category:** `{category}`\n"
                f"- **🔗 PDF Document:** [{paper_id}.pdf]({paper.pdf_url})\n\n"
                f"**📝 Abstract Summary:**\n"
                f"> {clean_summary}"
            )
            output.append(formatted_paper)
        return '\n\n---\n\n'.join(output)
    except Exception as e:
        return f"Error searching arXiv: {e}"

@tool
def get_weather(city: str) -> str:
    """Fetches real-time weather information for a given city name.
    Input should be a city name (e.g. 'Mumbai', 'London', 'New York', 'Tokyo').
    Returns current temperature in °C, humidity percentage, and wind speed.
    """
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geo_res = requests.get(geo_url, timeout=5).json()
        if not geo_res.get("results"):
            return f"Could not find location coordinates for '{city}'."
        
        loc = geo_res["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]
        city_name = loc.get("name", city)
        country = loc.get("country", "")

        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
        w_res = requests.get(weather_url, timeout=5).json()
        current = w_res.get("current", {})

        temp = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        wind = current.get("wind_speed_10m")

        return f"Weather in {city_name}, {country}: Temperature: {temp}°C, Humidity: {humidity}%, Wind Speed: {wind} km/h."
    except Exception as e:
        return f"Error fetching weather data: {e}"

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

    print("Initializing Tools (Search, Calculator, arXiv, Weather)...")
    search = GoogleSerperAPIWrapper()

    print("Initializing Gemini Model (gemini-3.5-flash-lite)...")
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        api_key=os.getenv("GOOGLE_API_KEY")
    )

    print("Creating Agent with Memory checkpointer...")
    memory = MemorySaver()

    # create_agent compiles a LangGraph agent that automatically executes tool calling
    agent = create_agent(
        model=llm,
        tools=[search.run, calculator, arxiv_search, get_weather],
        system_prompt=(
            "You are a helpful AI research assistant. "
            "You have access to Google Search for real-time web news and prices, "
            "a Calculator for math calculations, an arXiv Search tool for scientific papers, "
            "and a Weather tool for real-time weather details."
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

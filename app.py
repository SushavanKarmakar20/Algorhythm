from flask import Flask, render_template, request
from duckduckgo_search import DDGS
import os
import requests
import markdown
from markupsafe import Markup
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Load API credentials
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

print("OPENROUTER_API_KEY:", OPENROUTER_API_KEY)  # Debugging line

def format_date(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))  # if ends with 'Z'
        return dt.strftime("%B %d, %Y at %I:%M %p")
    except Exception:
        return iso_str 

def search_web(query):
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=25))
    except Exception as e:
        print(f"Web Search Error: {e}")
        return []

def search_news(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=25))
            for result in results:
                if 'date' in result:
                    result['date'] = format_date(result['date'])
            return results
    except Exception as e:
        print(f"News Search Error: {e}")
        return []

def get_openrouter_answer(topic):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",  
        "Content-Type": "application/json"
    }

    data = {
        "model": "z-ai/glm-4.5-air:free",
        "messages": [
            {"role": "user", "content": topic}
        ]
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        result = response.json()
        markdown_text = result["choices"][0]["message"]["content"]

        # ✅ Convert markdown to HTML
        html = markdown.markdown(markdown_text, extensions=["fenced_code", "tables"])
        return Markup(html)  # Mark it safe for rendering
    except Exception as e:
        print("OpenRouter Error:", e)
        return Markup(f"<p><strong>Error:</strong> {e}</p>")
    

@app.route("/", methods=["GET", "POST"])
def index():
    tab = "web"
    query = ""
    web_results = []
    news_results = []
    ai_result = ""
    answer_type = ""

    if request.method == "POST":
        tab = request.form.get("tab", "web")
        query = request.form.get("query", "").strip()

        if tab == "web":
            web_results = search_web(query)
        elif tab == "news":
            news_results = search_news(query)
        elif tab == "ai" and query:
            raw_response = get_openrouter_answer(query)
            ai_result = Markup(markdown.markdown(raw_response))

    return render_template("index.html", query=query, tab=tab,
                           web_results=web_results,
                           news_results=news_results,
                           ai_result=ai_result,
                           answer_type=answer_type)

if __name__ == "__main__":
    app.run(debug=True)

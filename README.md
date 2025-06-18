# Public Relations Sentiment Agent

A LangChain-powered AI agent that analyzes the public sentiment of companies based on recent news coverage. This full-stack project features a Flask frontend, a LangChain backend with Google’s Gemini 2.0 Flash, NewsAPI for article retrieval, TavilySearch for contextual lookup, and zero-shot classification for sentiment labeling.

## 🧠 Key Features

- **LangChain Agent with Tooling**: Uses custom tools (`get_news` and `TavilySearch`) to intelligently route and process user queries.
- **Sentiment Classification**: Applies `facebook/bart-large-mnli` to determine sentiment (positive, negative, neutral) for each article.
- **Caching System**: Implements SQLite to avoid redundant NewsAPI calls and log previous queries for efficiency.
- **Context Resolution**: Uses TavilySearch to fill gaps when prompts lack date ranges or sufficient information.
- **Qualitative Summaries**: Generates scaled sentiment scores and human-readable summaries using Gemini 2.0 Flash.

## 🛠 Tech Stack

- **Frontend**: Flask
- **Backend**: Python, LangChain, LangGraph
- **LLMs**: Gemini 2.0 Flash (Google), BART (Meta)
- **Data Tools**: NewsAPI, TavilySearch
- **Database**: SQLite

## 🚀 How It Works

1. **User Query** → The user asks a question about a company's recent public image.
2. **Context Check** → If the time frame is missing or vague, TavilySearch is used to clarify.
3. **News Fetching** → `get_news` checks the database for cached results and queries NewsAPI for missing data.
4. **Sentiment Analysis** → Each article is processed using zero-shot classification to assign a sentiment.
5. **Summary Generation** → The agent synthesizes results into a coherent PR summary with an overall sentiment score.


## 🧪 Example Prompt

> "What is the public sentiment around Tesla in the past few weeks?"

The agent will:
- Use `TavilySearch` to clarify dates if needed
- Fetch articles using `get_news`
- Label sentiment for each article
- Return a concise summary with a sentiment score

## 📌 Notes

- The agent only allows 1–3 `get_news` calls per prompt to prevent excessive API usage.
- Sentiment labels are based on article content, not just headlines or metadata.

from newsapi import NewsApiClient
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os
import sqlite3
from langchain_core.tools import tool
from datetime import timedelta, datetime, date
from typing import List
from langchain_tavily import TavilySearch
from langgraph.prebuilt import create_react_agent
from transformers import pipeline
import database
from langgraph.graph import START, MessagesState, StateGraph

workflow = StateGraph(state_schema=MessagesState)

load_dotenv()
model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
database.init_db()

@tool
def get_news(company_name: str, begin_date: str, end_date: str) -> List[dict]:
    '''
    This Tool Here checks the sqlite database to see if a query has already been done for a particular date, if it has not been done yet, 
    it then uses NewsAPI to fetch articles from the dates it needs, updateing our databse in the process. Afterwards, our tool returns
    every article from the requested dates
    '''
    def use_news_api(company_name, begin_date, end_date):
        news = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))
        all_articles = news.get_everything(
            q=company_name,
            from_param=begin_date,
            to=end_date,
            language='en',
            sort_by='relevancy'
        )['articles']

        conn, c = database.open_db()

        query_date = datetime.strptime(begin_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')

        while query_date <= end_dt:
            database.insert_query(c=c, company_name=company_name, query_date=query_date)
            query_date += timedelta(days=1)

        for article in all_articles:
            content = article.get('description') or article.get('content', '')
            candidate_labels = ["positive", "negative", "neutral"]
            result = classifier(content, candidate_labels)
            dominant_score = max(result['scores'])
            dominant_label = result['labels'][result['scores'].index(dominant_score)]

            database.insert_article(
                c=c,
                company_name=company_name,
                article=article,
                content=content,
                label=dominant_label,
                score=dominant_score
            )

        database.close_db(conn)

    begin_date_dt = datetime.strptime(begin_date, '%Y-%m-%d')
    end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')

    conn, c = database.open_db()

    min_query = "SELECT MIN(date) FROM query_log WHERE company = ?"
    min_result = database.query(c, min_query, (company_name,))
    min_available = datetime.strptime(min_result[0], '%Y-%m-%d') if min_result and min_result[0] else None

    max_query = "SELECT MAX(date) FROM query_log WHERE company = ?"
    max_result = database.query(c, max_query, (company_name,))
    max_available = datetime.strptime(max_result[0], '%Y-%m-%d') if max_result and max_result[0] else None

    database.close_db(conn)

    if min_available is None or max_available is None:
        use_news_api(company_name, begin_date, end_date)
    elif end_date_dt < min_available or begin_date_dt > max_available:
        use_news_api(company_name, begin_date, end_date)
    elif begin_date_dt < min_available:
        use_news_api(company_name, begin_date, (min_available - timedelta(days=1)).strftime('%Y-%m-%d'))
    elif end_date_dt > max_available:
        use_news_api(company_name, (max_available + timedelta(days=1)).strftime('%Y-%m-%d'), end_date)

    conn, c = database.open_db()
    article_query = """
        SELECT title, information, published_date, sentiment_score, sentiment_label
        FROM news_articles
        WHERE company = ?
          AND published_date BETWEEN ? AND ?
    """
    rows = database.query_multiple(c, article_query, (company_name, begin_date, end_date))
    database.close_db(conn)

    return [
        {
            "title": row[0],
            "information": row[1],
            "published_date": row[2],
            "sentiment_score": row[3],
            "sentiment_label": row[4]
        }
        for row in rows
    ]

basic_search_tool = TavilySearch(
    max_results=5,
    topic="general",
    # include_answer=False,
    # include_raw_content=False,
    # include_images=False,
    # include_image_descriptions=False,
    # search_depth="basic",
    # time_range="day",
    # include_domains=None,
    # exclude_domains=None
)

    
def create_agent():
    today = date.today().strftime("%B %d, %Y")
    agent_executor = create_react_agent(
        model=model, 
        tools=[get_news, basic_search_tool],
        prompt=(
            f"You are an expert in public relations (PR) analysis. Today is {today}. \n When given a company to investigate, your job is to "
            "analyze the overall sentiment of recent news coverage about the company.\n\n"
            "You can use the `get_news` tool to retrieve relevant news articles. This tool returns up to 100 articles per call. "
            "You may only call `get_news` once per company unless the date range is very large—in that case, you may call it up to 3 times.\n\n"
            "Based on the articles returned, provide a sentiment score and a qualitative assessment of the company's current PR outlook. "
            "Be sure to cite the main reasons behind the sentiment you assign.\n\n"
            "If you lack information needed to proceed (e.g., missing date ranges, unclear references), use the `basic_search_tool` to clarify "
            "the context using relevant keywords or events mentioned in the prompt.\n\n"
            "ENSURE ANY REQUEST YOU MAKE TO GET_NEWS IS WITHIN ONE MONTH, IF THEY REQUEST SOMETHING BEFORE TELL THEM YOU CANNOT\n\n"
            "Example: If a user asks about 'Tesla's recent earnings report,' but doesn't specify a date, use the context of the message along "
            "with the `basic_search_tool` to identify the relevant time frame before making further decisions.\n"
            "OUTPUT SHOULD BE A GENERAL SUMMARY OF WHATEVER THE QUESTION IS, DO NOT GIVE AN ARTICLE BY ARTICLE SUMMARY, ALSO MAKE SURE THE SENTIMENTS ARE SCALED"
        )
    )
    return agent_executor
def run_agent(agent_executor, message):
    return agent_executor.invoke({"messages": [{"role": "user", "content": message}]})


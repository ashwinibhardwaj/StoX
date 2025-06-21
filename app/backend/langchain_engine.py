# app/langchain_engine.py

import yfinance as yf
import requests
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# 1. Initialize LLM
llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="llama3-70b-8192"
)

# 2. Template for final insight
INSIGHT_TEMPLATE = """
You are an AI financial analyst. Given the following data about stock {ticker}, generate a detailed investment insight.

Include:
1. Company Summary
2. Financial Health (key metrics)
3. Stock Performance & Volatility
4. Market Sentiment or News Summary
5. Final Investment Recommendation (Buy/Hold/Sell) with reasoning

DATA:
{data}

INSIGHT:
"""

insight_prompt = PromptTemplate(
    input_variables=["ticker", "data"],
    template=INSIGHT_TEMPLATE,
)

insight_chain = LLMChain(llm=llm, prompt=insight_prompt)

# 3. Context Builder
def build_context_for_ticker(ticker, news_articles=[]):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        summary = info.get('longBusinessSummary', 'No summary available.')

        metrics = [
            f"Current Price: {info.get('currentPrice', 'N/A')}",
            f"Market Cap: {info.get('marketCap', 'N/A')}",
            f"PE Ratio: {info.get('trailingPE', 'N/A')}",
            f"EPS: {info.get('trailingEps', 'N/A')}",
            f"Dividend Yield: {info.get('dividendYield', 'N/A')}"
        ]

        hist = stock.history(period="1y")
        if not hist.empty:
            returns = hist['Close'].pct_change().dropna()
            volatility = returns.std() * (252 ** 0.5)
            total_return = (hist['Close'][-1] / hist['Close'][0]) - 1
            hist_summary = f"Total Return: {total_return * 100:.2f}%, Volatility: {volatility * 100:.2f}%"
        else:
            hist_summary = "No historical data available."

        news_summary = "\n".join([f"{a.get('title')} - {a.get('description', '')[:200]}" for a in news_articles]) or "No recent news found."

        context = f"""
Company Summary:
{summary}

Key Financial Metrics:
{chr(10).join(metrics)}

Stock Performance:
{hist_summary}

Recent News:
{news_summary}
"""
        return context.strip()
    except Exception as e:
        return f"Error fetching context for {ticker}: {e}"

# 4. Insight Generator
def generate_insight_for_ticker(ticker, news_articles):
    context = build_context_for_ticker(ticker, news_articles)
    return insight_chain.run({"ticker": ticker, "data": context})

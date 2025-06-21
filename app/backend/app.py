from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import requests
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime, timedelta
import json
from flask_mail import Mail, Message
import random
import pytz
import pandas as pd
import numpy as np
import yfinance as yf

from langchain_engine import generate_insight_for_ticker
import plotly.graph_objects as go
from flask_cors import CORS




load_dotenv()

app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')

app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Or your mail server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'ashwini.10521@gmail.com'
app.config['MAIL_PASSWORD'] = 'tngt yvdm byuy dxij'
app.config['MAIL_DEFAULT_SENDER'] = 'ashwini.10521@gmail.com'
mail = Mail(app)

# MySQL configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Ash96808',
    'database': 'stoxdb'
}


def generate_otp():
    return random.randint(100000, 999999)
# Login required decorator to protect the dashboard
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("You must log in to access this page.", "danger")
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function


def send_otp_email(user_email, otp):
    msg = Message('OTP Varification | StoX', recipients=[user_email])
    msg.body = f'Thanks for registering with us.Your OTP code is: {otp}'
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Prevent caching of sensitive pages
@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/register_page')
def register_page():
    return render_template('register.html')

@app.route('/home')
def home_page():
    return render_template('home.html',first_name=session['first_name'])

@app.route('/predictions')
def predictions_page():
    return render_template('predictions.html',first_name=session['first_name'])


@app.route('/otp_varification', methods=['GET', 'POST'])
def otp_varification():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match!", 'danger')
            return redirect(url_for('register_page'))

        # Establish connection
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Check if email exists
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            flash("Email already exists.", 'danger')
            return redirect(url_for('register_page'))
        
        otp = generate_otp()  # Generate OTP
        otp_sent_time = datetime.now()  # Capture OTP sent time
        
        # Save OTP and email in session
        session['otp'] = otp
        session['email'] = email
        session['first_name'] = first_name
        session['last_name'] = last_name
        session['password'] = password 
        session['otp_sent_time'] = otp_sent_time

        # Send OTP email
        if send_otp_email(email, otp):
            flash('OTP has been sent to your email. Please check your inbox and enter the OTP.', 'info')
            return render_template('otp_varification.html')  # Render OTP page for input
        else:
            flash('Failed to send OTP. Please try again.', 'danger')
            return render_template('register.html')
    
    return render_template('otp_varification.html')

@app.route('/verify_otp', methods=['POST', 'GET'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        otp = session.get('otp')
        email = session.get('email')
        otp_sent_time = session.get('otp_sent_time')

        if not otp or not otp_sent_time:
            flash('OTP session expired or invalid. Please request a new OTP.', 'danger')
            return redirect(url_for('register_page'))

        timezone = pytz.UTC  
        if otp_sent_time.tzinfo is None:  
            otp_sent_time = timezone.localize(otp_sent_time)

        now = datetime.now(timezone)  
        if now - otp_sent_time > timedelta(minutes=5):
            flash('OTP expired. Please request a new OTP.', 'danger')
            return render_template('register.html')
        
        # Verify OTP
        if str(otp) == entered_otp:
            first_name = session.get('first_name')
            last_name = session.get('last_name')
            email = session.get('email')
            password = session.get('password')
            register(first_name,last_name, email, password)
            flash('OTP verified successfully!', 'success')
            return redirect(url_for('login_page'))   
        else:
            flash('Invalid OTP, please try again.', 'danger')
            return render_template('otp_varification.html')  
    return render_template('otp_varification.html')

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Create a database connection
        connection = mysql.connector.connect(**db_config)
        if connection is None:
            flash("Database connection failed.", "danger")
            return redirect(url_for('login_page'))

        try:
            cursor = connection.cursor(dictionary=True)  # Use dictionary cursor for easy access to column names
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

            if user and check_password_hash(user['password'], password):
                # Store user details in the session
                session['user_id'] = user['id']
                session['email'] = user['email']
                session['first_name'] = user['first_name']

                flash(f"Welcome back, {user['first_name']}!", "success")
                return redirect(url_for('home_page'))
            else:
                flash("Invalid email or password. Please try again.", "danger")
                return redirect(url_for('login_page'))
        except mysql.connector.Error as e:
            print(f"MySQL error: {e}")
            flash("An error occurred while trying to log in. Please try again later.", "danger")
            return redirect(url_for('login_page'))
        finally:
            connection.close()

def register(first_name, last_name, email, password):
    try:
        # Establish connection
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)


        # Insert new user
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        cursor.execute("INSERT INTO users (first_name, last_name, email, password) VALUES (%s, %s, %s, %s)",
                        (first_name, last_name, email, hashed_password))
        conn.commit()
        flash("Account created successfully!", 'success')
        return redirect(url_for('login_page'))
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", 'danger')
    finally:
        cursor.close()
        conn.close()


@app.route("/dashboard")
@login_required
def dashboard():
    # Convert the "from" date to a proper format (YYYY-MM-DD)
    from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    # --------------------------
    # Fetch general trending news
    # --------------------------
    trending_params = {
        "q": "business OR finance OR stock prices OR market trends OR stock market OR stock performance",
        "language": "en",
        "sortBy": "publishedAt",
        "sources": "business-insider,bbc-news,reuters,the-wall-street-journal,bloomberg",
        "apiKey": NEWS_API_KEY,  # Your API key
        "pageSize": 9,
        "from": from_date
    }
    
    trending_response = requests.get(NEWS_API_URL, params=trending_params)
    if trending_response.status_code == 200:
        trending_articles = trending_response.json().get("articles", [])
    else:
        trending_articles = []

    # --------------------------------------------------
    # Fetch news for the user's subscribed companies
    # --------------------------------------------------
    # Retrieve subscribed company names from the database
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor(dictionary=True)
    query = "SELECT ticker FROM subscriptions WHERE user_id = %s"
    cursor.execute(query, (session['user_id'],))
    companies = [row['ticker'] for row in cursor.fetchall()]
    cursor.close()
    connection.close()

    subscribed_articles = []
    if companies:
        query_string = " OR ".join(companies)
        subscribed_params = {
            "q": query_string,
            "language": "en",
            "sortBy": "publishedAt",
            "apiKey": NEWS_API_KEY,
            "pageSize": 9,
            "from": from_date
        }
        subscribed_response = requests.get(NEWS_API_URL, params=subscribed_params)
        if subscribed_response.status_code == 200:
            subscribed_articles = subscribed_response.json().get("articles", [])
    
    return render_template(
        "dashboard.html", 
        trending_articles=trending_articles, 
        subscribed_articles=subscribed_articles,
        first_name=session['first_name']
    )

@app.route('/manage_subscription')
def manage_subscription():
    return render_template('manage_subscription.html', first_name=session['first_name'])


@app.route('/suggest_company', methods=['GET'])
@login_required
def suggest_company():
    """Return a list of company suggestions for a given company name query."""
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify({"suggestions": []})
    
    search_url = "https://query2.finance.yahoo.com/v1/finance/search"
    params = {'q': query, 'quotesCount': 5, 'newsCount': 0}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                      " AppleWebKit/537.36 (KHTML, like Gecko)"
                      " Chrome/90.0.4430.93 Safari/537.36"
    }
    try:
        response = requests.get(search_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        # Log e for debugging if needed
        return jsonify({"error": "Error retrieving suggestions."}), 500
    
    suggestions = []
    for item in data.get("quotes", []):
        ticker = item.get("symbol", "").upper().strip()
        company_name = item.get("longname") or item.get("shortname") or "Unknown Company"
        if ticker and company_name:
            suggestions.append({"ticker": ticker, "company_name": company_name})
    return jsonify({"suggestions": suggestions})

FINANCE_API_KEY = os.getenv('FINANCE_API_KEY')
FINANCE_API_URL = os.getenv('FINANCE_API_URL')

@app.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    """Subscribe the user to a ticker based on their selection from suggested companies."""
    ticker = request.form.get('ticker', '').upper().strip()
    company_name = request.form.get('company_name', '').strip()  # provided as hidden field

    if not ticker:
        flash("Please select a valid ticker from the suggestions.", "danger")
        return redirect(url_for('manage_subscription'))
    
    # Validate ticker by trying variations
    possible_tickers = [ticker, f"{ticker}.NS", f"{ticker}.BO"]
    valid_ticker = None
    for t in possible_tickers:
        stock = yf.Ticker(t)
        df = stock.history(period="1d")  # Fetch one day data
        if not df.empty:
            valid_ticker = t
            # Optionally, update company_name if available from Yahoo Finance info
            company_name = stock.info.get("longName", company_name)
            break

    if not valid_ticker:
        flash("The selected ticker could not be validated on Yahoo Finance.", "danger")
        return redirect(url_for('manage_subscription'))
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Check if subscription already exists
        cursor.execute(
            "SELECT * FROM subscriptions WHERE user_id = %s AND ticker = %s",
            (session['user_id'], valid_ticker)
        )
        if cursor.fetchone():
            flash("You are already subscribed to this ticker.", "warning")
            return redirect(url_for('manage_subscription'))

        # Insert subscription into the database
        cursor.execute(
            "INSERT INTO subscriptions (user_id, ticker, company_name) VALUES (%s, %s, %s)",
            (session['user_id'], valid_ticker, company_name)
        )
        conn.commit()
        flash(f"Successfully subscribed to {company_name} ({valid_ticker}).", "success")
    except mysql.connector.Error as e:
        flash(f"Database error: {e}", "danger")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

    return redirect(url_for('manage_subscription'))


@app.route('/unsubscribe', methods=['POST'])
@login_required
def unsubscribe():
    """Handle unsubscription from a ticker."""
    ticker = request.form.get('ticker', '').upper().strip()

    if not ticker:
        flash("Please provide a valid ticker symbol.", "danger")
        return redirect(url_for('manage_subscription'))

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Delete the subscription from the database
        cursor.execute(
            "DELETE FROM subscriptions WHERE user_id = %s AND ticker = %s",
            (session['user_id'], ticker)
        )
        if cursor.rowcount > 0:
            conn.commit()
            flash(f"Successfully unsubscribed from {ticker}.", "success")
        else:
            flash(f"No subscription found for {ticker}.", "warning")

        return redirect(url_for('manage_subscription'))

    except mysql.connector.Error as e:
        flash(f"Database error: {e}", "danger")
    finally:
        cursor.close()
        conn.close()


@app.route('/subscriptions')
@login_required
def subscriptions():
    """Display user's subscriptions."""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Fetch user's subscriptions
        cursor.execute(
            "SELECT ticker, company_name, created_at FROM subscriptions WHERE user_id = %s",
            (session['user_id'],)
        )
        subscriptions = cursor.fetchall()

        return render_template(
            'subscriptions.html',
            subscriptions=subscriptions,
            first_name=session['first_name']
        )

    except mysql.connector.Error as e:
        flash(f"Database error: {e}", "danger")
    finally:
        cursor.close()
        conn.close()


@app.route('/trend_charts')
def trend_charts():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))  # Redirect to login if user is not logged in
    
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor(dictionary=True)
    
    query = "SELECT ticker FROM subscriptions WHERE user_id = %s"
    cursor.execute(query, (user_id,))
    tickers = [row['ticker'] for row in cursor.fetchall()]
    
    connection.close()

    # Render the template and pass the tickers list to it
    return render_template('trend_charts.html', tickers=tickers,first_name=session['first_name'])


# Route to fetch user-subscribed tickers
@app.route('/get_tickers')
def get_tickers():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not logged in"}), 403

    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor(dictionary=True)
    
    query = "SELECT ticker FROM subscriptions WHERE user_id = %s"
    cursor.execute(query, (user_id,))
    tickers = [row['ticker'] for row in cursor.fetchall()]
    
    connection.close()
    return jsonify(tickers)

@app.route('/get_company_names')
def get_company_names():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not logged in"}), 403

    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor(dictionary=True)
    
    query = "SELECT ticker, company_name FROM subscriptions WHERE user_id = %s"
    cursor.execute(query, (user_id,))
    subscriptions = cursor.fetchall()
    
    connection.close()
    return jsonify(subscriptions)


# Route to fetch stock data for a selected ticker
@app.route('/get_stock_data/<ticker>')
def get_stock_data(ticker):
    try:
        range_option = request.args.get('range', 'daily').lower()
        stock = yf.Ticker(ticker)
        df = stock.history(period="max")
        if df.empty:
            return jsonify({"error": "No data available for this stock"}), 404

        df = df.reset_index()
        df['Date'] = pd.to_datetime(df['Date'])

        # Resample data if needed
        if range_option == 'monthly':
            df = df.resample('ME', on='Date').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).reset_index()
        elif range_option == 'yearly':
            df = df.resample('YE', on='Date').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).reset_index()
        
        # Calculate technical indicators if enough data exists
        if len(df) >= 50:
            # Moving averages
            df['SMA20'] = df['Close'].rolling(window=20).mean()
            df['SMA50'] = df['Close'].rolling(window=50).mean()

            # Exponential moving averages for MACD
            df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
            df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = df['EMA12'] - df['EMA26']
            df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

            # Bollinger Bands (20-day)
            df['BB_Middle'] = df['SMA20']
            df['BB_std'] = df['Close'].rolling(window=20).std()
            df['BB_upper'] = df['BB_Middle'] + 2 * df['BB_std']
            df['BB_lower'] = df['BB_Middle'] - 2 * df['BB_std']

            # RSI Calculation (14-day)
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            df['RSI'] = 100 - (100 / (1 + rs))
        else:
            df['SMA20'] = np.nan
            df['SMA50'] = np.nan
            df['EMA12'] = np.nan
            df['EMA26'] = np.nan
            df['MACD'] = np.nan
            df['MACD_signal'] = np.nan
            df['BB_Middle'] = np.nan
            df['BB_upper'] = np.nan
            df['BB_lower'] = np.nan
            df['RSI'] = np.nan

        # Convert Date to string
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')

        # Basic statistics
        stats = {
            "avg_close": round(df["Close"].mean(), 2),
            "median_close": round(df["Close"].median(), 2),
            "max_close": round(df["Close"].max(), 2),
            "min_close": round(df["Close"].min(), 2),
            "std_close": round(df["Close"].std(), 2),
            "total_volume": int(df["Volume"].sum())
        }
        
        # Generate extended insights
        insights = []
        # RSI-based insights
        if not df['RSI'].isnull().all():
            latest_rsi = df['RSI'].iloc[-1]
            if latest_rsi > 70:
                insights.append("RSI is above 70, indicating overbought conditions. Consider waiting for a pullback.")
            elif latest_rsi < 30:
                insights.append("RSI is below 30, suggesting oversold conditions. This could be a buying opportunity.")
            else:
                insights.append("RSI is in a neutral zone.")

        # MACD-based insights
        if not df['MACD'].isnull().all() and not df['MACD_signal'].isnull().all():
            latest_macd = df['MACD'].iloc[-1]
            latest_macd_signal = df['MACD_signal'].iloc[-1]
            if latest_macd > latest_macd_signal:
                insights.append("MACD is above its signal line, indicating bullish momentum.")
            elif latest_macd < latest_macd_signal:
                insights.append("MACD is below its signal line, indicating bearish momentum.")

        # Moving average crossover insight
        if not df['SMA20'].isnull().all() and not df['SMA50'].isnull().all():
            if df['SMA20'].iloc[-1] > df['SMA50'].iloc[-1] and df['SMA20'].iloc[-2] < df['SMA50'].iloc[-2]:
                insights.append("A bullish crossover occurred: SMA20 crossed above SMA50.")
            elif df['SMA20'].iloc[-1] < df['SMA50'].iloc[-1] and df['SMA20'].iloc[-2] > df['SMA50'].iloc[-2]:
                insights.append("A bearish crossover occurred: SMA20 crossed below SMA50.")

        # Bollinger Bands insight
        if not df['BB_upper'].isnull().all() and not df['BB_lower'].isnull().all():
            latest_close = df['Close'].iloc[-1]
            bb_upper = df['BB_upper'].iloc[-1]
            bb_lower = df['BB_lower'].iloc[-1]
            if latest_close >= bb_upper:
                insights.append("Price has touched or exceeded the upper Bollinger Band. This could indicate an overbought market or potential reversal.")
            elif latest_close <= bb_lower:
                insights.append("Price has touched or fallen below the lower Bollinger Band. This could signal oversold conditions.")

        # Volume insight
        if not df['Volume'].isnull().all():
            latest_volume = df['Volume'].iloc[-1]
            avg_volume = df['Volume'].mean()
            if latest_volume > 1.5 * avg_volume:
                insights.append("The latest trading volume is significantly higher than average, which may signal a major move or news event.")
            else:
                insights.append("Trading volume is near average, indicating steady market participation.")

        # Price momentum insight
        if len(df) >= 2:
            price_change = (df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100
            if price_change > 2:
                insights.append(f"Price increased by {price_change:.2f}% in the last period, showing strong upward momentum.")
            elif price_change < -2:
                insights.append(f"Price decreased by {abs(price_change):.2f}% in the last period, indicating downward momentum.")
            else:
                insights.append("Price change is modest, suggesting stable conditions.")

        return jsonify({
            "dates": df["Date"].tolist(),
            "open": df["Open"].tolist(),
            "high": df["High"].tolist(),
            "low": df["Low"].tolist(),
            "close": df["Close"].tolist(),
            "prices": df["Close"].tolist(),
            "volume": df["Volume"].tolist(),
            "SMA20": df["SMA20"].fillna("").tolist(),
            "SMA50": df["SMA50"].fillna("").tolist(),
            "BB_middle": df["BB_Middle"].fillna("").tolist(),
            "BB_upper": df["BB_upper"].fillna("").tolist(),
            "BB_lower": df["BB_lower"].fillna("").tolist(),
            "MACD": df["MACD"].fillna("").tolist(),
            "MACD_signal": df["MACD_signal"].fillna("").tolist(),
            "RSI": df["RSI"].fillna("").tolist(),
            "stats": stats,
            "insights": insights
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/logout')
def logout():
    session.clear()  # Clear session data
    flash("You have been logged out.", "success")
    return redirect(url_for('login_page'))


NEWS_API_KEY = "7bfef36f6dba4d4b89e7dcb74c3e1877"  
NEWS_API_URL = "https://newsapi.org/v2/everything"

@app.route("/get_news")
def get_news():
    # --- Trending News ---
    trending_params = {
        "api_token": NEWS_API_KEY,  
        "categories": "business,finance,stocks",  # General market news categories
        "language": "en",
        "limit": 9,
        "sort_by": "published_at"
    }
    trending_response = requests.get(NEWS_API_URL, params=trending_params)
    if trending_response.status_code == 200:
        trending_articles = trending_response.json().get("articles", [])
    else:
        trending_articles = []
    
    # --- Subscribed Ticker News ---
    # Get user's subscribed tickers from the database
    subscribed_tickers = get_company_names()
    # Join tickers into a comma-separated string (if there are any)
    ticker_symbols = ",".join(subscribed_tickers) if subscribed_tickers else ""
    
    subscribed_params = {
        "api_token": NEWS_API_KEY,
        "symbols": ticker_symbols,  # News for the user's tickers
        "language": "en",
        "limit": 5,
        "sort_by": "published_at"
    }
    subscribed_response = requests.get(NEWS_API_URL, params=subscribed_params)
    if subscribed_response.status_code == 200:
        subscribed_articles = subscribed_response.json().get("articles", [])
    else:
        subscribed_articles = []
    
    return render_template("dashboard.html", 
                           trending_articles=trending_articles, 
                           subscribed_articles=subscribed_articles)



def get_news_for_ticker(ticker):
    url = NEWS_API_URL
    params = {
        "api_token": NEWS_API_KEY,
        "symbols": ticker,
        "language": "en",
        "limit": 5,
        "sort_by": "published_at"
    }
    response = requests.get(url, params=params)
    return response.json().get("articles", []) if response.ok else []


# Setup HuggingFace pipelines

def summarize_news_articles(articles, max_articles=3):
    summarized_news = []
    for article in articles[:max_articles]:
        description = article.get('description', '')[:512]
        if not description:
            continue
        try:
            summary = news_summarizer(description)[0]['summary_text']
            sentiment = sentiment_analyzer(description)[0]
            summarized_news.append(f"{summary} (Sentiment: {sentiment['label']})")
        except:
            continue
    return "News Highlights:\n" + "\n".join(summarized_news) if summarized_news else ""

def generate_stock_chart(ticker, hist):
    if hist.empty:
        return ""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name='Close'))
    fig.update_layout(title=f"{ticker} Price Trend", xaxis_title='Date', yaxis_title='Price ($)')
    chart_path = f"static/charts/{ticker}_{datetime.now().strftime('%Y%m%d%H%M%S')}.html"
    fig.write_html(chart_path)
    return chart_path

def fetch_context_for_ticker(ticker, period="1y", articles=[]):
    context_docs = []
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Summary
        summary = f"{ticker} Summary: {info.get('longBusinessSummary', 'No summary available.')}"
        context_docs.append(summary)

        # Financial metrics
        metrics = [
            f"Current Price: {info.get('currentPrice', 'N/A')}",
            f"Market Cap: {info.get('marketCap', 'N/A')}",
            f"PE Ratio: {info.get('trailingPE', 'N/A')}",
            f"EPS: {info.get('trailingEps', 'N/A')}",
            f"Forward PE: {info.get('forwardPE', 'N/A')}",
            f"ROE: {info.get('returnOnEquity', 'N/A')}",
            f"Debt to Equity: {info.get('debtToEquity', 'N/A')}",
            f"Dividend Yield: {info.get('dividendYield', 'N/A')}",
            f"Institutional Holdings: {info.get('heldPercentInstitutions', 'N/A')}"
        ]
        context_docs.append("Financial Metrics:\n" + "\n".join(metrics))

        # Analyst Recommendations
        try:
            recs = stock.recommendations
            if not recs.empty:
                latest_recs = recs.tail(5)[['Firm', 'To Grade', 'From Grade', 'Action']]
                context_docs.append("Recent Analyst Recommendations:\n" + latest_recs.to_string())
        except:
            pass

        # Historical Stock Data
        hist = stock.history(period=period)
        if not hist.empty:
            close_prices = hist['Close']
            daily_returns = close_prices.pct_change().dropna()
            volatility = daily_returns.std() * np.sqrt(252)
            total_return = (close_prices[-1] / close_prices[0]) - 1
            ma_50 = close_prices.rolling(50).mean().iloc[-1] if len(close_prices) >= 50 else None
            ma_200 = close_prices.rolling(200).mean().iloc[-1] if len(close_prices) >= 200 else None

            hist_summary = (
                f"Historical Performance ({period}):\n"
                f"Price Range: ${close_prices.min():.2f} - ${close_prices.max():.2f}\n"
                f"Current Price: ${close_prices[-1]:.2f}\n"
                f"Total Return: {total_return*100:.2f}%\n"
                f"Volatility (Annualized): {volatility*100:.2f}%\n"
            )
            if ma_50: hist_summary += f"50-day MA: ${ma_50:.2f}\n"
            if ma_200: hist_summary += f"200-day MA: ${ma_200:.2f}\n"

            context_docs.append(hist_summary)
            generate_stock_chart(ticker, hist)

        # News Analysis
        if articles:
            news_summary = summarize_news_articles(articles)
            if news_summary:
                context_docs.append(news_summary)

    except Exception as e:
        context_docs.append(f"Error fetching data: {str(e)}")

    return context_docs


@app.route('/generate_insights', methods=['POST'])
def generate_insights():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not logged in'}), 403

    data = request.get_json()
    ticker = data.get('ticker')

    if not ticker:
        return jsonify({'error': 'No ticker provided'}), 400

    try:
        news_articles = get_news_for_ticker(ticker)
        insight = generate_insight_for_ticker(ticker, news_articles)
    except Exception as e:
        insight = f"Error generating insight: {str(e)}"

    return jsonify({'insight': insight})



@app.route('/insights')
def insights_page():
    tickers = get_tickers()
    return render_template('insights.html',tickers=tickers)




# Predictions
from keras.models import load_model
import joblib
from flask import request, jsonify
import yfinance as yf
import pandas as pd
import numpy as np

model = load_model("models/keras_new_model.h5", compile=False)
scaler = joblib.load("models/price_scaler.pkl")  # Trained scaler

@app.route("/get_predicted_data")
def get_predicted_data():
    ticker = request.args.get("ticker")
    if not ticker:
        return jsonify({"error": "Ticker not provided"}), 400

    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo")
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()

        if len(df) < 100:
            return jsonify({"error": "Not enough data to make predictions"}), 400

        # === Scale the full dataset ===
        scaled = scaler.transform(df)

        # === Build prediction input ===
        X = []
        for i in range(60, len(scaled)):
            X.append(scaled[i-60:i])

        X = np.array(X)

        # === Predict ===
        preds_scaled = model.predict(X)

        # === Inverse scale predicted close prices ===
        predicted_prices = []
        for val in preds_scaled:
            dummy = np.zeros((1, 5))
            dummy[0, 3] = val[0]
            inv = scaler.inverse_transform(dummy)
            predicted_prices.append(float(inv[0, 3]))

        # === Actual and predicted prices aligned ===
        actual_prices = df['Close'].tolist()[60:]
        actual_dates = df.index[60:].strftime('%Y-%m-%d').tolist()

        return jsonify({
            "dates": actual_dates,
            "actual_prices": actual_prices,
            "predicted_prices": predicted_prices
        })

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)

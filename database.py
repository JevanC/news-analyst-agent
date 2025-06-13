import sqlite3
def init_db():
    conn = sqlite3.connect("news_cache.db")
    c = conn.cursor()
    conn.execute("PRAGMA journal_mode=WAL;")
    c.execute('''
        CREATE TABLE IF NOT EXISTS news_articles(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              company TEXT,
              title TEXT,
              information TEXT,
              published_date TEXT,
              sentiment_label TEXT,
              sentiment_score REAL,
              UNIQUE(company, title, published_date)
              )         
''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS query_log(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              company TEXT,
              date TEXT,
              UNIQUE(company, date)
              )         
''')
    conn.commit()
    conn.close()

def open_db():
    conn = sqlite3.connect("news_cache.db")
    c = conn.cursor()
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn, c

def close_db(conn):
    conn.commit()
    conn.close()

def insert_query(c, company_name : str, query_date):
    c.execute('''
    INSERT OR IGNORE INTO query_log (company, date)
    VALUES (?, ?)
    ''', (company_name, query_date.strftime('%Y-%m-%d')))

def insert_article(c, company_name, article, content, label, score):
    c.execute('''
        INSERT OR IGNORE INTO news_articles (company, title, information, published_date, sentiment_label, sentiment_score)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
        company_name,
        article['title'],
        content,
        article['publishedAt'].split("T")[0],
        label,
        score
    ))

def get_articles(c, company_name, begin_date, end_date):
        c.execute('''
            SELECT title, information, published_date, sentiment_score, sentiment_label
            FROM news_articles
            WHERE company = ?
              AND published_date BETWEEN ? AND ?
        ''', (company_name, begin_date, end_date))
        return c.fetchall()

def query(c, query, *args):
    if args:
        return c.execute(query, args[0]).fetchone()
    return c.execute(query).fetchone()

def query_multiple(c, query, *args):
    if args:
        return c.execute(query, args[0]).fetchall()
    return c.execute(query).fetchall()

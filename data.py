import os
import csv

from flask import Flask, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL", "sqlite:///database.db"))
db = scoped_session(sessionmaker(bind=engine))

def make_tables():
    db.execute('''CREATE TABLE IF NOT EXISTS users (username VARCHAR(16) NOT NULL, password VARCHAR(64) NOT NULL, join_date text,
                PRIMARY KEY(username))''')
    db.execute('''CREATE TABLE IF NOT EXISTS email (mail VARCHAR(64) NOT NULL, username VARCHAR(16) NOT NULL, FOREIGN KEY(username)
                REFERENCES users(username) ON DELETE CASCADE ON UPDATE CASCADE, PRIMARY KEY(mail, username), UNIQUE(mail, username))''')
    db.execute('''CREATE TABLE IF NOT EXISTS assets (id SERIAL PRIMARY KEY, type VARCHAR(40), name VARCHAR(50),
                currency VARCHAR(10), symbol VARCHAR(30), UNIQUE(name))''')
    db.execute('''CREATE TABLE IF NOT EXISTS investment (id SERIAL PRIMARY KEY, username VARCHAR(16) NOT NULL,
                asset VARCHAR(50), buy_price FLOAT, quantity INTEGER, date text, FOREIGN KEY(username) REFERENCES users(username) ON DELETE CASCADE ON UPDATE CASCADE, FOREIGN KEY(asset) REFERENCES assets(name) ON DELETE CASCADE ON UPDATE CASCADE)''')
    db.execute('''CREATE TABLE IF NOT EXISTS returns (id SERIAL PRIMARY KEY, username VARCHAR(16) NOT NULL,
                asset VARCHAR(50), buy_price FLOAT, sell_price FLOAT, quantity INTEGER, buy_date text, sell_date text, FOREIGN KEY(username) REFERENCES users(username) ON DELETE CASCADE ON UPDATE CASCADE, FOREIGN KEY(asset) REFERENCES assets(name) ON DELETE CASCADE ON UPDATE CASCADE)''')
    db.commit()
    db.close()

def insert_assets():
    f = open("stock data.csv")
    reader = csv.reader(f)
    count = 0
    currency = "INR"
    for name, symbol, type in reader:
        if count == 0:
            count += 1
        else:
            db.execute("INSERT INTO assets (type, name, currency, symbol) VALUES (:type, :name, :currency, :symbol)", {"type": type, "name": name, "currency": currency, "symbol": symbol})
            print(f"{count}. {name} Inserted")
            count += 1

    db.commit()
    db.close()

def create_tables():
    make_tables()
    table_data = db.execute("SELECT * FROM assets").fetchall()
    db.close()
    if len(table_data) <= 0:
        insert_assets()

create_tables()

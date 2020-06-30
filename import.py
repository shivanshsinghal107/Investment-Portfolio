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

db.execute('''CREATE TABLE IF NOT EXISTS users (username VARCHAR(16) NOT NULL, password VARCHAR(64) NOT NULL, join_date text,
            PRIMARY KEY(username))''')
db.execute('''CREATE TABLE IF NOT EXISTS email (mail VARCHAR(64) NOT NULL, username VARCHAR(16) NOT NULL, FOREIGN KEY(username)
            REFERENCES users(username) ON DELETE CASCADE ON UPDATE CASCADE, PRIMARY KEY(mail, username))''')
db.execute('''CREATE TABLE IF NOT EXISTS assets (id INTEGER PRIMARY KEY AUTOINCREMENT, type VARCHAR(40), name VARCHAR(50),
            currency VARCHAR(5), symbol VARCHAR(10), yf_symbol VARCHAR(15), yf_name VARCHAR(50), url VARCHAR(100))''')
db.execute('''CREATE TABLE IF NOT EXISTS investment (id INTEGER PRIMARY KEY AUTOINCREMENT, username VARCHAR(16) NOT NULL,
            asset VARCHAR(50), buy_price FLOAT, quantity INTEGER, date text, FOREIGN KEY(username) REFERENCES users(username) ON DELETE CASCADE ON UPDATE CASCADE, FOREIGN KEY(asset) REFERENCES assets(name) ON DELETE CASCADE ON UPDATE CASCADE)''')
db.execute('''CREATE TABLE IF NOT EXISTS returns (id INTEGER PRIMARY KEY AUTOINCREMENT, username VARCHAR(16) NOT NULL,
            asset VARCHAR(50), buy_price FLOAT, sell_price FLOAT, quantity INTEGER, date text, FOREIGN KEY(username) REFERENCES users(username) ON DELETE CASCADE ON UPDATE CASCADE, FOREIGN KEY(asset) REFERENCES assets(name) ON DELETE CASCADE ON UPDATE CASCADE)''')
db.commit()

def insert_assets():
    print("Inserting Commodities in the assets table")
    type = "commodities"
    f = open("commodities.csv")
    reader = csv.reader(f)
    count = 0
    for symbol, name, url, yf_symbol, currency, yf_name in reader:
        if count == 0:
            count += 1
        else:
            db.execute("INSERT INTO assets (type, name, currency, symbol, yf_symbol, yf_name, url) VALUES (:type, :name, :currency, :symbol, :yf_symbol, :yf_name, :url)", {"type": type, "name": name, "currency": currency, "symbol": symbol, "yf_symbol": yf_symbol, "yf_name": yf_name, "url": url})
            print(f"{count}. {name} Inserted")
            count += 1

    print()

    print("Inserting Forex Currencies in the assets table")
    type = "forex currencies"
    f = open("forex_currencies.csv")
    reader = csv.reader(f)
    count = 0
    for symbol, name, url, yf_symbol, currency, yf_name in reader:
        if count == 0:
            count += 1
        else:
            db.execute("INSERT INTO assets (type, name, currency, symbol, yf_symbol, yf_name, url) VALUES (:type, :name, :currency, :symbol, :yf_symbol, :yf_name, :url)", {"type": type, "name": name, "currency": currency, "symbol": symbol, "yf_symbol": yf_symbol, "yf_name": yf_name, "url": url})
            print(f"{count}. {name} Inserted")
            count += 1
    db.commit()

insert_assets()
db.close()

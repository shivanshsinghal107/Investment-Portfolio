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
    db.execute('''CREATE TABLE IF NOT EXISTS assets (id INTEGER PRIMARY KEY, type VARCHAR(100), name VARCHAR(100),
                currency VARCHAR(100), symbol VARCHAR(100), UNIQUE(name))''')
    db.execute('''CREATE TABLE IF NOT EXISTS investment (id INTEGER PRIMARY KEY, username VARCHAR(16) NOT NULL,
                asset VARCHAR(100), buy_price FLOAT, quantity INTEGER, date text, FOREIGN KEY(username) REFERENCES users(username) ON DELETE CASCADE ON UPDATE CASCADE, FOREIGN KEY(asset) REFERENCES assets(name) ON DELETE CASCADE ON UPDATE CASCADE)''')
    db.execute('''CREATE TABLE IF NOT EXISTS returns (id INTEGER PRIMARY KEY, username VARCHAR(16) NOT NULL,
                asset VARCHAR(100), buy_price FLOAT, sell_price FLOAT, quantity INTEGER, buy_date text, sell_date text, FOREIGN KEY(username) REFERENCES users(username) ON DELETE CASCADE ON UPDATE CASCADE, FOREIGN KEY(asset) REFERENCES assets(name) ON DELETE CASCADE ON UPDATE CASCADE)''')
    db.commit()
    db.close()

def insert_assets():
    print("Inserting small-cap stocks")
    type = "small-cap"
    f = open("small cap.csv")
    reader = csv.reader(f)
    count = 0
    currency = "INR"
    for name, symbol in reader:
        if count == 0:
            count += 1
        else:
            db.execute("INSERT INTO assets (type, name, currency, symbol) VALUES (:type, :name, :currency, :symbol)", {"type": type, "name": name, "currency": currency, "symbol": symbol})
            print(f"{count}. {name} Inserted")
            count += 1
    print()

    print("Inserting mid-cap stocks")
    type = "mid-cap"
    f = open("mid cap.csv")
    reader = csv.reader(f)
    count = 0
    currency = "INR"
    for name, symbol in reader:
        if count == 0:
            count += 1
        else:
            db.execute("INSERT INTO assets (type, name, currency, symbol) VALUES (:type, :name, :currency, :symbol)", {"type": type, "name": name, "currency": currency, "symbol": symbol})
            print(f"{count}. {name} Inserted")
            count += 1

    print()

    print("Inserting large-cap stocks")
    type = "large-cap"
    f = open("large cap.csv")
    reader = csv.reader(f)
    count = 0
    currency = "INR"
    for name, symbol in reader:
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

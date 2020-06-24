import os
import datetime
import yfinance as yf
from pandas_datareader import data as pdr

from flask import Flask, session, request, render_template, redirect
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

yf.pdr_override()

@app.route("/", methods = ['GET', 'POST'])
def index():
    if request.method == 'GET':
        if session.get("logged_in"):
            return render_template("index.html", loginstatus = "True", curruser = session["username"])
        else:
            return render_template("index.html", loginstatus = "False")
    else:
        category = request.form.get("asset").lower().replace(" ", "+")
        return redirect(f"/{category}")

@app.route("/register", methods = ['GET', 'POST'])
def register():
    if session.get("logged_in"):
        return "<script>alert('You are already logged in, log out first'); window.location = 'http://127.0.0.1:5000/';</script>"
    else:
        if request.method == 'POST':
            username = request.form.get("username")
            password = request.form.get("password")
            email = request.form.get("email")
            date = datetime.datetime.utcnow()
            db.execute("INSERT INTO users (username, password, join_date) VALUES (:username, :password, :join_date)",
                        {"username": username, "password": password, "join_date": date})
            db.execute("INSERT INTO email (mail, username) VALUES (:mail, :username)", {"mail": email, "username": username})
            db.commit()
            session["logged_in"] = True
            session["username"] = username
            db.close()
            return "<script>alert('Registered Successfully');window.location = 'http://127.0.0.1:5000/';</script>"
        else:
            return render_template("register.html")

@app.route("/login", methods = ['GET', 'POST'])
def login():
    if session.get("logged_in"):
        return "<script>alert('You are already logged in'); window.location = 'http://127.0.0.1:5000/';</script>"
    else:
        if request.method == 'POST':
            username = request.form.get("username")
            password = request.form.get("password")
            data = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchall()
            if len(data) > 0:
                if data[0].password == password:
                    session["logged_in"] = True
                    session["username"] = username
                    db.close()
                    return "<script>alert('Login Successful');window.location = 'http://127.0.0.1:5000/';</script>"
                else:
                    db.close()
                    return "<script>alert('Invalid password');window.location = 'http://127.0.0.1:5000/login';</script>"
            else:
                db.close()
                return "<script>alert('Please register first');window.location = 'http://127.0.0.1:5000/register';</script>"
        else:
            return render_template("login.html")

@app.route("/logout", methods = ['GET', 'POST'])
def logout():
    print(session.keys())
    session.clear()
    print(session.keys())
    return redirect("http://127.0.0.1:5000")

@app.route("/<category>", methods = ['GET', 'POST'])
def get_assets(category):
    c = category.replace("+", " ")
    data = db.execute("SELECT * FROM assets WHERE type = :type", {"type": c}).fetchall()
    prices = []
    for d in data:
        price = pdr.get_data_yahoo(d.yf_symbol, start = str(datetime.datetime.utcnow())[:10])
        if len(price) > 1:
            prices.append(round(price.Close[1], 2))
        elif len(price) > 0:
            prices.append(round(price.Close[0], 2))
        else:
            prices.append("NA")
    db.close()
    if session.get("logged_in"):
        return render_template("asset.html", loginstatus = "True", curruser = session["username"], category = c.title(), data = data, prices = prices)
    else:
        return render_template("asset.html", loginstatus = "False", category = c.title(), data = data, prices = prices)

@app.route("/buy/<id>/<price>", methods = ['GET', 'POST'])
def buy(id, price):
    if request.method == 'POST':
        quantity = int(request.form.get("quantity"))
        username = session["username"]
        d = str(datetime.datetime.utcnow())[:10].split("-")
        date = f"{d[2]}-{d[1]}-{d[0]}"
        asset = db.execute("SELECT * FROM assets WHERE id = :id", {"id": id}).fetchall()[0]
        db.execute("INSERT INTO investment (username, asset, curr_price, quantity, date) VALUES (:username, :asset, :curr_price, :quantity, :date)", {"username": username, "asset": asset.name, "curr_price": price, "quantity": quantity, "date": date})
        print(f"Invested in {asset.name}")
        db.commit()
        db.close()
        return "<script>alert('Investment Successful'); window.location = window.history.back();</script>"
    else:
        return "<script>alert('Method not allowed'); window.location = window.history.back();</script>"

@app.route("/portfolio", methods = ['GET', 'POST'])
def portfolio():
    if session.get("logged_in"):
        invs = db.execute("SELECT * FROM investment WHERE username = :username ORDER BY date DESC", {"username": session["username"]}).fetchall()
        print(len(invs))
        symbols = []
        prices = []
        currency = []
        type = []
        change = []
        pchange = []
        net_pl = 0
        total = 0
        for i in invs:
            d = db.execute("SELECT * FROM assets WHERE name = :name", {"name": i.asset}).fetchall()[0]
            price = pdr.get_data_yahoo(d.yf_symbol, start = str(datetime.datetime.utcnow())[:10])
            if len(price) > 1:
                p = round(price.Close[1], 2)
                prices.append(p)
                change.append(round(p - i.curr_price, 2))
                pchange.append(round((1 - i.curr_price/p), 4))
                net_pl += (p - i.curr_price) * i.quantity
            elif len(price) > 0:
                p = round(price.Close[0], 2)
                prices.append(p)
                change.append(round(p - i.curr_price, 2))
                pchange.append(round((1 - i.curr_price/p), 4))
                net_pl += (p - i.curr_price) * i.quantity
            else:
                prices.append("NA")
                change.append("NA")
                pchange.append("NA")
            symbols.append(d.symbol)
            currency.append(d.currency)
            type.append(d.type)
            total += i.curr_price * i.quantity
        db.close()
        return render_template("portfolio.html", curruser = session["username"], invs = invs, symbols = symbols, prices = prices, currency = currency, type = type, change = change, pchange = pchange, net_pl = round(net_pl, 2), total = total)
    else:
        return "<script>alert('Login first'); window.location = 'http://127.0.0.1:5000/login';</script>"

#@app.route("/<category>/<asset>", methods = ['GET', 'POST'])
#def display_asset(category, asset):

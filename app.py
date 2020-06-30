import os
import datetime
import yfinance as yf
import pandas as pd
# these below two lines are for avoiding a runtime error
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from pandas_datareader import data as pdr
from collections import Counter
from base64 import b64encode
from io import BytesIO

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

# changing color settings in matplotlib for dark theme of website
plt.rcParams.update({
    "lines.color": "white",
    "patch.edgecolor": "white",
    "text.color": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "lightgray",
    "axes.labelcolor": "white",
    "xtick.color": "white",
    "ytick.color": "white",
    "grid.color": "lightgray",
    "figure.facecolor": "black",
    "figure.edgecolor": "black",
    "savefig.facecolor": "black",
    "savefig.edgecolor": "black"})

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
        date = str(datetime.datetime.utcnow())
        asset = db.execute("SELECT * FROM assets WHERE id = :id", {"id": id}).fetchall()[0]
        db.execute("INSERT INTO investment (username, asset, buy_price, quantity, date) VALUES (:username, :asset, :buy_price, :quantity, :date)", {"username": username, "asset": asset.name, "buy_price": price, "quantity": quantity, "date": date})
        print(f"Invested in {asset.name}")
        db.commit()
        db.close()
        return "<script>alert('Investment Successful'); window.location = window.history.back();</script>"
    else:
        return "<script>alert('Method not allowed'); window.location = window.history.back();</script>"

@app.route("/sell/<id>/<price>", methods = ['GET', 'POST'])
def sell(id, price):
    if request.method == 'POST':
        quantity = int(request.form.get("quantity"))
        username = session["username"]
        date = str(datetime.datetime.utcnow())
        inv = db.execute("SELECT * FROM investment WHERE id = :id", {"id": id}).fetchall()[0]
        db.execute("INSERT INTO returns (username, asset, buy_price, sell_price, quantity, date) VALUES (:username, :asset, :buy_price, :sell_price, :quantity, :date)", {"username": username, "asset": inv.asset, "buy_price": inv.buy_price, "sell_price": price, "quantity": quantity, "date": date})
        if quantity < inv.quantity:
            db.execute("UPDATE investment SET quantity = :quantity WHERE id = :id", {"quantity": (inv.quantity-quantity), "id": id})
        print(f"Sold {inv.asset}")
        db.commit()
        db.close()
        return "<script>alert('Sold'); window.location = window.history.back();</script>"
    else:
        return "<script>alert('Method not allowed'); window.location = window.history.back();</script>"

@app.route("/portfolio/investment", methods = ['GET', 'POST'])
def investments():
    if session.get("logged_in"):
        username = session["username"]
        invs = db.execute("SELECT * FROM investment WHERE username = :username ORDER BY date DESC", {"username": username}).fetchall()
        print(len(invs))
        dates = []
        symbols = []
        prices = []
        currency = []
        type = []
        pchange = []
        net_pl = 0
        total = 0
        for i in invs:
            if i.quantity > 0:
                d = db.execute("SELECT * FROM assets WHERE name = :name", {"name": i.asset}).fetchall()[0]
                price = pdr.get_data_yahoo(d.yf_symbol, start = str(datetime.datetime.utcnow())[:10])
                if len(price) > 1:
                    p = round(price.Close[1], 2)
                    prices.append(p)
                    pchange.append(round((1 - i.buy_price/p)*100, 4))
                    net_pl += (p - i.buy_price) * i.quantity
                elif len(price) > 0:
                    p = round(price.Close[0], 2)
                    prices.append(p)
                    pchange.append(round((1 - i.buy_price/p)*100, 4))
                    net_pl += (p - i.buy_price) * i.quantity
                else:
                    prices.append("NA")
                    pchange.append("NA")
                da = i.date[:10].split("-")
                date = f"{da[2]}-{da[1]}-{da[0]}"
                dates.append(date)
                symbols.append(d.symbol)
                currency.append(d.currency)
                type.append(d.type)
                total += i.buy_price * i.quantity
        db.close()
        return render_template("investment.html", curruser = username, dates = dates, invs = invs, symbols = symbols, prices = prices, currency = currency, type = type, pchange = pchange, net_pl = round(net_pl, 2), total = total)
    else:
        return "<script>alert('Login first'); window.location = 'http://127.0.0.1:5000/login';</script>"

@app.route("/portfolio/return", methods = ['GET', 'POST'])
def returns():
    if session.get("logged_in"):
        username = session["username"]
        rets = db.execute("SELECT * FROM returns WHERE username = :username ORDER BY date DESC", {"username": username}).fetchall()
        print(len(rets))
        dates = []
        symbols = []
        currency = []
        type = []
        pchange = []
        net_pl = 0
        for r in rets:
            d = db.execute("SELECT * FROM assets WHERE name = :name", {"name": r.asset}).fetchall()[0]
            pchange.append(round((1 - r.buy_price/r.sell_price)*100, 4))
            da = r.date[:10].split("-")
            date = f"{da[2]}-{da[1]}-{da[0]}"
            dates.append(date)
            symbols.append(d.symbol)
            currency.append(d.currency)
            type.append(d.type)
            net_pl += r.quantity * (r.sell_price - r.buy_price)
        db.close()
        return render_template("return.html", curruser = username, dates = dates, rets = rets, symbols = symbols, currency = currency, type = type, pchange = pchange, net_pl = round(net_pl, 2))
    else:
        return "<script>alert('Login first'); window.location = 'http://127.0.0.1:5000/login';</script>"

@app.route("/portfolio", methods = ['GET', 'POST'])
def portfolio():
    if session.get("logged_in"):
        username = session["username"]
        invs = db.execute("SELECT * FROM investment WHERE username = :username", {"username": username}).fetchall()
        category = []
        assets = []
        symbols = []
        for i in invs:
            a = db.execute("SELECT * FROM assets WHERE name = :name", {"name": i.asset}).fetchall()[0]
            category.append(a.type)
            if i.asset not in assets:
                assets.append(i.asset)
                symbols.append(a.yf_symbol)
        fig = plt.figure(figsize = (12, 6))
        d = dict(Counter(category))
        d['goverment bonds'] = 3
        d['corporate bonds'] = 2
        d['mid-cap stocks'] = 2
        plt.pie(d.values(), labels = d.keys(), autopct = '%1.1f%%')
        img = BytesIO()
        fig.savefig(img, format = 'png', bbox_inches = 'tight')
        img.seek(0)
        encoded_pc = b64encode(img.getvalue())

        fig1 = plt.figure(figsize = (12, 6))
        count = 0
        for s in symbols:
            data = pdr.get_data_yahoo(s, start = '2020-01-01')
            plt.plot((data['Close'] / data['Close'].iloc[0] * 100), label = assets[count])
            count += 1
        plt.xlabel('YEAR')
        plt.ylabel('PRICE')
        plt.legend()
        plt.grid()
        img1 = BytesIO()
        fig1.savefig(img1, format = 'png', bbox_inches = 'tight')
        img1.seek(0)
        encoded_graph = b64encode(img1.getvalue())
        db.close()
        return render_template("portfolio.html", curruser = username, pie_chart = encoded_pc.decode('utf-8'), graph = encoded_graph.decode('utf-8'))
    else:
        return "<script>alert('Login first'); window.location = 'http://127.0.0.1:5000/login';</script>"

@app.route("/<category>/<asset>/<show>", methods = ['GET', 'POST'])
def display_asset(category, asset, show):
    a = db.execute("SELECT * FROM assets WHERE name = :name", {"name": asset}).fetchall()[0]
    today = str(datetime.datetime.utcnow())
    month = today[5:7]
    if show == 'daily':
        if int(month) <= 10:
            m = '0' + str(int(month) - 1)
        else:
            m = str(int(month) - 1)
        last_date = today[:5] + m + '-' + today[8:10]
    elif show == 'monthly':
        last_date = '2020-01-01'
    else:
        last_date = '2015' + today[4:10]
    data = pdr.get_data_yahoo(a.yf_symbol, start = last_date)
    fig = plt.figure(figsize = (10, 5))
    plt.plot((data['Close'] / data['Close'].iloc[0] * 100))
    plt.fill_between(data.index, data.Close)
    plt.xlabel('DATE')
    plt.ylabel('PRICE')
    plt.xticks(rotation = 45)
    img = BytesIO()
    fig.savefig(img, format = 'png', bbox_inches = 'tight')
    img.seek(0)
    chart = b64encode(img.getvalue())
    curr_price = round(data.Close[0], 3)
    return render_template("stock.html", asset = asset, category = category, symbol = a.symbol, curr_price = curr_price, currency = a.currency, chart = chart.decode('utf-8'), show = show.title())

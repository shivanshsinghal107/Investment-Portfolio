import os
import smtplib
import datetime
import yfinance as yf
import numpy as np
import pandas as pd
# these below two lines are for avoiding a runtime error
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta
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
password = os.getenv("password")

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

def send_mail(email, subject, body):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    # EHLO means ESMTP - Extended Simple Mail Transfer Protocol
    server.ehlo()
    server.starttls()
    server.ehlo()

    server.login('help.quantizers@gmail.com', password) # see the video tutorial from README.md file

    msg = f"Subject: {subject}\n\n{body}"

    server.sendmail('help.quantizers@gmail.com', email, msg)
    print("HEY, EMAIL HAS BEEN SENT!")

    server.quit()

@app.route("/", methods = ['GET', 'POST'])
def index():
    if request.method == 'GET':
        if session.get("logged_in"):
            return render_template("index.html", loginstatus = "True", curruser = session["username"])
        else:
            return render_template("index.html", loginstatus = "False")
    else:
        category = request.form.get("asset").lower().replace("-", "+")
        return redirect(f"/{category}")

@app.route("/register", methods = ['GET', 'POST'])
def register():
    if session.get("logged_in"):
        return "<script>alert('You are already logged in, log out first'); window.location = 'https://quantizers.herokuapp.com/';</script>"
    else:
        if request.method == 'POST':
            username = request.form.get("username")
            password = request.form.get("password")
            email = request.form.get("email")
            date = str(datetime.datetime.utcnow())
            if (username == "") or (password == "") or (email == ""):
                return "<script>alert('Fill all the fields'); window.location = window.history.back();</script>"
            data = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchall()
            if len(data) > 0:
                db.close()
                return "<script>alert('Username already exists, choose another'); window.location = window.history.back();</script>"
            db.execute("INSERT INTO users (username, password, join_date) VALUES (:username, :password, :join_date)",
                        {"username": username, "password": password, "join_date": date})
            db.execute("INSERT INTO email (mail, username) VALUES (:mail, :username)", {"mail": email, "username": username})
            db.commit()
            session["logged_in"] = True
            session["username"] = username
            db.close()
            subject = 'Getting started with Quantizers'
            body = '''Hey there fellow Investor!\n\nWe wish you the best of luck for your coming financial ventures as you join the Quantizers family. It takes a lot of courage to invest your hard-earned money in a domain of unknown nature. For this specific reason, we have created this web app but if you have any doubts or want some more info on the methodology used, drop at help.quantizers@gmail.com or through feedback form through the web app.\n\nAnd kindly go through the Terms and Conditions before performing any actual transaction -\n\nThe QUANTIZERS or any people in this venture are not registered with SEBI. This web app is solely meant to provide you with performance simulations on a portfolio that you will select based according to your financial intelligence. We are not certified under IA regulation in any manner. Therefore we are not liable for your money, and this platform is based on virtual money; hence you are not required to put in any of your Real Cash. Our optimization models will suggest the best possible portfolio to invest in through various mathematical portfolio optimization models, but it's all on you whether to go with it or not. We will show you the real-world possibility scenarios of multiple assets, and that's all.\n\nThis web application is entirely public and free to use.\n\nWe suggest you make your financial decision on your own choice and not solely based on our methods. All the investments that you make are subjected to market risks, so do thorough research before investing your hard-earned money. In any case, as we are not handling your real cash, therefore we won't be liable for any accusations. Any future complaints about any loss or damage will not be considered.\n\nKeep Investing!!\nThank You\nTeam Quantizers'''
            send_mail(email, subject, body)
            return "<script>alert('Registered Successfully, check your mail');window.location = 'https://quantizers.herokuapp.com/';</script>"
        else:
            return render_template("register.html")

@app.route("/login", methods = ['GET', 'POST'])
def login():
    if session.get("logged_in"):
        return "<script>alert('You are already logged in'); window.location = 'https://quantizers.herokuapp.com/';</script>"
    else:
        if request.method == 'POST':
            username = request.form.get("username")
            password = request.form.get("password")
            if (username == "") or (password == ""):
                return "<script>alert('Please fill both fields'); window.location = window.history.back();</script>"
            data = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchall()
            if len(data) > 0:
                if data[0].password == password:
                    session["logged_in"] = True
                    session["username"] = username
                    db.close()
                    return "<script>alert('Login Successful');window.location = 'https://quantizers.herokuapp.com/';</script>"
                else:
                    db.close()
                    return "<script>alert('Invalid password');window.location = 'https://quantizers.herokuapp.com/login';</script>"
            else:
                db.close()
                return "<script>alert('Please register first');window.location = 'https://quantizers.herokuapp.com/register';</script>"
        else:
            return render_template("login.html")

@app.route("/logout", methods = ['GET', 'POST'])
def logout():
    print(session.keys())
    session.clear()
    print(session.keys())
    return redirect("https://quantizers.herokuapp.com/")

@app.route("/tnc")
def terms_and_cond():
    return render_template("info.html", info = 'Terms & Conditions')

@app.route("/about")
def about_us():
    return render_template("info.html", info = 'About Us')

@app.route("/feedback", methods = ['GET', 'POST'])
def feedback():
    if session.get("logged_in"):
        if request.method == 'GET':
            return render_template("feedback.html")
        else:
            username = session["username"]
            feedback = request.form.get("feedback")
            subject = f'Feedback from {session["username"]}'
            send_mail("help.quantizers@gmail.com", subject, feedback)
            return "<script>alert('Feedback submitted successfully'); window.location = 'https://quantizers.herokuapp.com/';</script>"
    else:
        return "<script>alert('Please login first'); window.location = 'https://quantizers.herokuapp.com/login';</script>"

@app.route("/<category>", methods = ['GET', 'POST'])
def get_assets(category):
    c = category.replace("+", "-")
    data = db.execute("SELECT * FROM assets WHERE type = :type", {"type": c}).fetchall()
    syms = [d.symbol for d in data]
    today = str(datetime.date.today())
    curr_data = pdr.get_data_yahoo(syms, start = today)['Close']
    if curr_data.empty:
        today = str(datetime.date.today() + relativedelta(days=-1))
        curr_data = pdr.get_data_yahoo(syms, start = today)['Close']
    if curr_data.empty:
        today = str(datetime.date.today() + relativedelta(days=-2))
        curr_data = pdr.get_data_yahoo(syms, start = today)['Close']
    prices = []
    for d in data:
        if str(curr_data.iloc[-1][d.symbol]) == 'nan':
            try:
                if str(curr_data.iloc[-2][d.symbol]) != 'nan':
                    prices.append(round(curr_data.iloc[-2][d.symbol], 2))
                else:
                    p = pdr.get_data_yahoo(d.symbol, start = str(datetime.date.today() + relativedelta(months=-1)))['Close']
                    prices.append(round(p.iloc[-1], 2))
            except:
                p = pdr.get_data_yahoo(d.symbol, start = str(datetime.date.today() + relativedelta(months=-1)))['Close']
                prices.append(round(p.iloc[-1], 2))
        else:
            price = round(curr_data.iloc[-1][d.symbol], 2)
        prices.append(price)
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
        db.execute("INSERT INTO returns (username, asset, buy_price, sell_price, quantity, buy_date, sell_date) VALUES (:username, :asset, :buy_price, :sell_price, :quantity, :buy_date, :sell_date)", {"username": username, "asset": inv.asset, "buy_price": inv.buy_price, "sell_price": price, "quantity": quantity, "buy_date": inv.date, "sell_date": date})
        if quantity < inv.quantity:
            db.execute("UPDATE investment SET quantity = :quantity WHERE id = :id", {"quantity": (inv.quantity-quantity), "id": id})
        elif quantity == inv.quantity:
            db.execute("DELETE FROM investment WHERE id = :id", {"id": id})
        print(f"Sold {inv.asset}")
        db.commit()
        db.close()
        return "<script>alert('Sold'); window.location = document.referrer;</script>"
    else:
        return "<script>alert('Method not allowed'); window.location = window.history.back();</script>"

@app.route("/portfolio/investment", methods = ['GET', 'POST'])
def investments():
    if session.get("logged_in"):
        username = session["username"]
        invs = db.execute("SELECT * FROM investment WHERE username = :username ORDER BY date DESC", {"username": username}).fetchall()
        if len(invs) > 0:
            dates = []
            prices = []
            type = []
            pchange = []
            net_pl = 0
            total = 0
            total_inv = 0
            syms = []
            betas = []
            #cagrs = []
            #rois = []
            start = str(datetime.date.today() + relativedelta(years=-5))
            for i in invs:
                if i.quantity > 0:
                    d = db.execute("SELECT * FROM assets WHERE name = :name", {"name": i.asset}).fetchall()[0]
                    syms.append(d.symbol)
                    type.append(d.type)
            syms.append('^NSEI')
            syms.append('^BSESN')
            curr_data = pdr.get_data_yahoo(syms, start = start)['Close']
            for i in invs:
                d = db.execute("SELECT * FROM assets WHERE name = :name", {"name": i.asset}).fetchall()[0]
                if str(curr_data.iloc[-1][d.symbol]) == 'nan':
                    price = round(curr_data.iloc[-2][d.symbol], 2)
                    #cagr = round(((curr_data.iloc[-2][d.symbol]/curr_data.iloc[0][d.symbol])**(1/5) - 1)*100, 2)
                    #roi = round(((curr_data.iloc[-2][d.symbol]/curr_data.iloc[0][d.symbol]) - 1)*100, 2)
                else:
                    price = round(curr_data.iloc[-1][d.symbol], 2)
                    #cagr = round(((curr_data.iloc[-1][d.symbol]/curr_data.iloc[0][d.symbol])**(1/5) - 1)*100, 2)
                    #roi = round(((curr_data.iloc[-1][d.symbol]/curr_data.iloc[0][d.symbol]) - 1)*100, 2)
                if d.symbol[-2:] == 'BO':
                    index = '^BSESN'
                else:
                    index = '^NSEI'
                data = curr_data[[d.symbol, index]]
                returns = data.pct_change()
                cov = returns.cov()
                covar = cov[d.symbol].iloc[1]
                var = cov[index].iloc[1]
                beta = round(covar/var, 2)
                betas.append(beta)
                #rois.append(f"{roi}%")
                #cagrs.append(cagr)
                prices.append(price)
            for i in range(len(invs)):
                if invs[i].quantity > 0:
                    p = prices[i]
                    pchange.append(round((p/invs[i].buy_price - 1)*100, 2))
                    net_pl += p * invs[i].quantity
                    da = invs[i].date[:10].split("-")
                    date = f"{da[2]}-{da[1]}-{da[0]}"
                    dates.append(date)
                    total += invs[i].buy_price * invs[i].quantity
            total_inv = total
            rets = db.execute("SELECT * FROM returns WHERE username = :username", {"username": username}).fetchall()
            if len(rets) > 0:
                for r in rets:
                    total_inv += r.buy_price * r.quantity
            db.close()
            roi = round(((net_pl-total)/total)*100, 2)
            cagr = round(((net_pl/total)**(1/5)-1)*100, 2)
            return render_template("investment.html", curruser = username, dates = dates, invs = invs, symbols = syms, prices = prices, type = type, pchange = pchange, betas = betas, net_pl = int(net_pl), total = int(total), total_inv = int(total_inv), roi = roi, cagr = cagr)
        else:
            db.close()
            return render_template("investment.html", curruser = username, dates = [], invs = [], symbols = [], prices = [], type = [], pchange = [], betas = [], net_pl = 0, total = 0, total_inv = 0, roi = 0, cagr = 0)
    else:
        return "<script>alert('Login first'); window.location = 'https://quantizers.herokuapp.com/login';</script>"

@app.route("/portfolio/return", methods = ['GET', 'POST'])
def returns():
    if session.get("logged_in"):
        username = session["username"]
        rets = db.execute("SELECT * FROM returns WHERE username = :username ORDER BY sell_date DESC", {"username": username}).fetchall()
        print(len(rets))
        buy_dates = []
        sell_dates = []
        symbols = []
        type = []
        pchange = []
        net_pl = 0
        for r in rets:
            d = db.execute("SELECT * FROM assets WHERE name = :name", {"name": r.asset}).fetchall()[0]
            pchange.append(round((1 - r.buy_price/r.sell_price)*100, 2))
            da = r.buy_date[:10].split("-")
            date = f"{da[2]}-{da[1]}-{da[0]}"
            buy_dates.append(date)
            da = r.sell_date[:10].split("-")
            date = f"{da[2]}-{da[1]}-{da[0]}"
            sell_dates.append(date)
            symbols.append(d.symbol)
            type.append(d.type)
            net_pl += r.quantity * (r.sell_price - r.buy_price)
        db.close()
        return render_template("return.html", curruser = username, buy_dates = buy_dates, sell_dates = sell_dates, rets = rets, symbols = symbols, type = type, pchange = pchange, net_pl = int(net_pl))
    else:
        return "<script>alert('Login first'); window.location = 'https://quantizers.herokuapp.com/login';</script>"

@app.route("/portfolio", methods = ['GET', 'POST'])
def portfolio():
    if session.get("logged_in"):
        username = session["username"]
        invs = db.execute("SELECT * FROM investment WHERE username = :username", {"username": username}).fetchall()
        if len(invs) > 0:
            category = []
            assets = []
            symbols = []
            for i in invs:
                a = db.execute("SELECT * FROM assets WHERE name = :name", {"name": i.asset}).fetchall()[0]
                category.append(a.type)
                if i.asset not in assets:
                    assets.append(i.asset)
                    symbols.append(a.symbol)
            fig = plt.figure(figsize = (12, 6))
            d = dict(Counter(category))
            plt.pie(d.values(), labels = d.keys(), autopct = '%1.1f%%')
            img = BytesIO()
            fig.savefig(img, format = 'png', bbox_inches = 'tight')
            img.seek(0)
            encoded_pc = b64encode(img.getvalue())
            plt.close(fig)

            curr_data = pdr.get_data_yahoo(symbols, start = "2020-01-01")['Adj Close']
            # if there's only one symbol then curr_data is a series not dataframe, & series does not have columns attribute
            if len(symbols) == 1:
                curr_data = pd.DataFrame(curr_data)
            stock_graphs = []
            count = 0
            for c in curr_data.columns:
                fig1 = plt.figure(figsize = (12, 6))
                plt.plot(curr_data[c], c = np.random.rand(3,))
                plt.xlabel('DATE')
                plt.ylabel('PRICE')
                plt.title(assets[count].upper())
                #plt.fill_between(curr_data.index, curr_data[c])
                plt.grid()
                img1 = BytesIO()
                fig1.savefig(img1, format = 'png', bbox_inches = 'tight')
                img1.seek(0)
                encoded_graph = b64encode(img1.getvalue())
                stock_graphs.append(encoded_graph.decode('utf-8'))
                count += 1
                plt.close(fig1)
            db.close()
            return render_template("portfolio.html", curruser = username, investments = 'True', pie_chart = encoded_pc.decode('utf-8'), stock_graphs = stock_graphs)
        else:
            db.close()
            return render_template("portfolio.html", curruser = username, investments = 'False')
    else:
        return "<script>alert('Login first'); window.location = 'https://quantizers.herokuapp.com/login';</script>"

@app.route("/<category>/<asset>/<show>", methods = ['GET', 'POST'])
def display_asset(category, asset, show):
    print(asset)
    a = db.execute("SELECT * FROM assets WHERE name = :name", {"name": asset}).fetchall()[0]
    #today = str(datetime.datetime.utcnow())[:10]
    #month = today[5:7]
    if show == 'daily':
        last_date = str(datetime.date.today() + relativedelta(months=-3))
    elif show == 'monthly':
        last_date = str(datetime.date.today() + relativedelta(months=-12))
    else:
        last_date = str(datetime.date.today() + relativedelta(years=-5))
    data = pdr.get_data_yahoo(a.symbol, start = last_date)
    fig = plt.figure(figsize = (12, 6))
    plt.plot(data['Adj Close'])
    plt.fill_between(data.index, data['Adj Close'])
    plt.xlabel('DATE')
    plt.ylabel('PRICE')
    plt.xticks(rotation = 45)
    img = BytesIO()
    fig.savefig(img, format = 'png', bbox_inches = 'tight')
    img.seek(0)
    chart = b64encode(img.getvalue())
    plt.close(fig)
    curr_price = round(data.Close[-1], 2)
    db.close()
    return render_template("stock.html", asset = asset, category = category, symbol = a.symbol, curr_price = curr_price, currency = a.currency, chart = chart.decode('utf-8'), show = show.title())

@app.route("/input/featured", methods = ['GET', 'POST'])
def take_input_featured():
    if session.get("logged_in"):
        username = session["username"]
        type = 'featured'
        syms = ['ALEMBICLTD.NS', 'CHAMANSEQ.BO', 'DLTNCBL.BO', 'ESTER.NS', 'FAZE3Q.BO', 'FOODSIN.BO', 'GANESHBE.BO', 'INTENTECH.BO', 'JPASSOCIAT.BO', 'NEOINFRA.BO', 'RAMANEWS.NS', 'SALSTEEL.NS', 'SEAMECLTD.BO', 'TATACHEM.NS', 'TIGLOB.BO', 'UFO.NS', 'UNIDT.BO', 'YUKEN.BO']
        if request.method == 'POST':
            money = request.form.get("money")
            stock_str = ""
            for s in syms:
                stock_str += s + ", "
            print(stock_str)
            return redirect(f"https://quantizers.herokuapp.com/optimization/{type}/{stock_str}/{money}")
        else:
            return render_template("input.html", curruser = username, type = type, syms = syms)
    else:
        return "<script>alert('Login first'); window.location = 'https://quantizers.herokuapp.com/login';</script>"

@app.route("/input/custom", methods = ['GET', 'POST'])
def take_input_custom():
    if session.get("logged_in"):
        username = session["username"]
        type = 'custom'
        if request.method == 'POST':
            money = request.form.get("money")
            stocks = request.form.getlist("stocks")
            if len(stocks) >= 5:
                stock_str = ""
                for s in stocks:
                    stock_str += s + ", "
                print(stock_str)
                return redirect(f"https://quantizers.herokuapp.com/optimization/{type}/{stock_str}/{money}")
            else:
                return "<script>alert('Select at least 5 stocks'); window.location = window.history.back();</script>"
        else:
            stocks = db.execute("SELECT * FROM assets").fetchall()
            syms = [s.symbol for s in list(stocks)]
            syms = sorted(syms)
            db.close()
            return render_template("input.html", curruser = username, type = type, syms = syms)
    else:
        return "<script>alert('Login first'); window.location = 'https://quantizers.herokuapp.com/login';</script>"

@app.route("/optimization/<type>/<stocks>/<money>", methods = ['GET', 'POST'])
def optimization(type, stocks, money):
    if session.get("logged_in"):
        username = session["username"]
        syms = stocks.split(", ")[:-1]
        k = len(syms)
        if 'custom' in type:
            start = str(datetime.date.today() + relativedelta(years=-5))
            #try:
            stock_data = pdr.get_data_yahoo(syms, start = start)['Adj Close']
            returns = stock_data.pct_change()
            #mean_daily_returns = np.array(returns.mean()).reshape(-1, 1)
            cov = returns.cov()
            stds = np.array(returns.std()).reshape(-1, 1)
            product_std = np.dot(stds, stds.T)
            cov_mat = np.array(cov)
            corr = cov_mat / product_std
            ret = (stock_data.iloc[-1]/stock_data.iloc[0] - 1)
            annual_return = np.array(ret).reshape(-1, 1)

            # max sharpe ratio
            risk_free_rate = 0.04
            best_wts = maximize_sharpe_ratio(annual_return, risk_free_rate, cov, k)
            sharpe_wts = []
            sharpe_per_wts = []
            for i in range(len(best_wts)):
                wt = round(best_wts[i, 0], 2)
                sharpe_wts.append(wt)
                sharpe_per_wts.append(str(int(wt*100)) + " %")

            # minimum portfolio variance
            best_wts = minimize_portfolio_variance(corr, stds, annual_return, k)
            var_wts = []
            var_per_wts = []
            for i in range(len(best_wts)):
                wt = round(best_wts[i, 0], 2)
                var_wts.append(wt)
                var_per_wts.append(str(int(wt*100)) + " %")

            # monthly, quarterly, half-yearly, yearly
            try:
                min_port_var = 1.30
                max_port_var = 1.40
                best_wts = maximize_annual_return(stock_data, stds, corr, annual_return, min_port_var, max_port_var, k)
                max_return_wts = []
                max_return_per_wts = []
                for i in range(len(best_wts)):
                    wt = round(best_wts[i, 0], 2)
                    max_return_wts.append(wt)
                    max_return_per_wts.append(str(int(wt*100)) + " %")
                markowitz = 'pass'
            except:
                max_return_wts = []
                max_return_per_wts = []
                for i in range(k):
                    max_return_wts.append(0)
                    max_return_per_wts.append('NA')
                markowitz = 'fail'

            today = str(datetime.date.today())
            curr_data = pdr.get_data_yahoo(syms, start = today)['Close']
            if curr_data.empty:
                today = str(datetime.date.today() + relativedelta(days=-1))
                curr_data = pdr.get_data_yahoo(syms, start = today)['Close']
            if curr_data.empty:
                today = str(datetime.date.today() + relativedelta(days=-2))
                curr_data = pdr.get_data_yahoo(syms, start = today)['Close']
            # python list comprehension
            curr_price = []
            for col in curr_data.columns:
                if str(curr_data.iloc[-1][col]) == 'nan':
                    curr_price.append(round(curr_data.iloc[-2][col], 2))
                else:
                    curr_price.append(round(curr_data.iloc[-1][col], 2))
            #curr_price = [round(price, 2) for price in list(curr_data.iloc[-1])]
            sharpe_money = [round(w*int(money), 2) for w in sharpe_wts]
            sharpe_units = [int(mon / price) for mon, price in zip(sharpe_money, curr_price)]
            var_money = [round(w*int(money), 2) for w in var_wts]
            var_units = [int(mon / price) for mon, price in zip(var_money, curr_price)]
            max_return_money = [round(w*int(money), 2) for w in max_return_wts]
            max_return_units = [int(mon / price) for mon, price in zip(max_return_money, curr_price)]

            return render_template("optimize.html", curruser = username, sharpe_wts = sharpe_per_wts, var_wts = var_per_wts, max_return_wts = max_return_per_wts, sharpe_units = sharpe_units, var_units = var_units, max_return_units = max_return_units, curr_price = curr_price, syms = list(stock_data.columns), markowitz = markowitz)
            #except:
            #    return render_template("error.html")
        else:
            sharpe_wts = [0.012330895, 0.005640655, 0.051854235, 0.020031155, 0.028242825, 0.007840155, 0.028735295, 0.055140065, 0.003773405, 0.020111765, 0.049593095, 0.013737555, 0.21786576500000002, 0.066526685, 0.079822865, 0.0035624949999999997, 0.06653349500000001, 0.26865759499999997]
            sharpe_per_wts = []
            for i in range(len(sharpe_wts)):
                wt = round(sharpe_wts[i], 2)
                sharpe_per_wts.append(str(int(wt*100)) + " %")
            var_wts = [0.11722865833333333, 0.03976156833333334, 0.11924990833333333, 0.028351518333333336, 0.06151221833333334, 0.029295838333333334, 0.04914447833333334, 0.06701142833333333, 0.054304638333333335, 0.06907119833333333, 0.03455894833333333, 0.052545578333333336, 0.029733098333333336, 0.031027288333333337, 0.048869148333333334, 0.08272458833333333, 0.03605392833333333, 0.04955596833333334]
            var_per_wts = []
            for i in range(len(var_wts)):
                wt = round(var_wts[i], 2)
                var_per_wts.append(str(int(wt*100)) + " %")
            max_return_wts = [0.014196323333333333, 0.031347023333333335, 0.020847673333333334, 0.04473478333333333, 0.09538094333333333, 0.009485933333333335, 0.03635488333333334, 0.054638563333333334, 0.009309223333333335, 0.028263193333333336, 0.026650463333333336, 0.015281823333333335, 0.05987788333333334, 0.017066653333333334, 0.10751989333333332, 0.010396533333333334, 0.10789077333333333, 0.31075743333333333]
            max_return_per_wts = []
            for i in range(len(max_return_wts)):
                wt = round(max_return_wts[i], 2)
                max_return_per_wts.append(str(int(wt*100)) + " %")

            today = str(datetime.date.today())
            curr_data = pdr.get_data_yahoo(syms, start = today)['Close']
            if curr_data.empty:
                today = str(datetime.date.today() + relativedelta(days=-1))
                curr_data = pdr.get_data_yahoo(syms, start = today)['Close']
            if curr_data.empty:
                today = str(datetime.date.today() + relativedelta(days=-2))
                curr_data = pdr.get_data_yahoo(syms, start = today)['Close']
            curr_data = curr_data[syms]
            # python list comprehension
            curr_price = []
            for col in curr_data.columns:
                if str(curr_data.iloc[-1][col]) == 'nan':
                    try:
                        if str(curr_data.iloc[-2][col]) != 'nan':
                            curr_price.append(round(curr_data.iloc[-2][col], 2))
                        else:
                            p = pdr.get_data_yahoo(col, start = str(datetime.date.today() + relativedelta(months=-1)))['Close']
                            #print(p.tail())
                            curr_price.append(round(p.iloc[-1], 2))
                    except:
                        p = pdr.get_data_yahoo(col, start = str(datetime.date.today() + relativedelta(months=-1)))['Close']
                        #print(p.tail())
                        curr_price.append(round(p.iloc[-1], 2))
                else:
                    curr_price.append(round(curr_data.iloc[-1][col], 2))
            #curr_price = [round(price, 2) for price in list(curr_data.iloc[-1])]
            sharpe_money = [round(w*int(money), 2) for w in sharpe_wts]
            sharpe_units = [int(mon / price) for mon, price in zip(sharpe_money, curr_price)]
            var_money = [round(w*int(money), 2) for w in var_wts]
            var_units = [int(mon / price) for mon, price in zip(var_money, curr_price)]
            max_return_money = [round(w*int(money), 2) for w in max_return_wts]
            max_return_units = [int(mon / price) for mon, price in zip(max_return_money, curr_price)]

            return render_template("optimize.html", curruser = username, sharpe_wts = sharpe_per_wts, var_wts = var_per_wts, max_return_wts = max_return_per_wts, sharpe_units = sharpe_units, var_units = var_units, max_return_units = max_return_units, curr_price = curr_price, syms = syms, markowitz = 'pass')
    else:
        return "<script>alert('Login first'); window.location = 'https://quantizers.herokuapp.com/login';</script>"

@app.route("/buy_optimized", methods = ['GET', 'POST'])
def buy_optimized():
    if request.method == 'POST':
        username = session["username"]
        symbols = request.args.getlist("symbols")
        prices = request.args.getlist("curr_price")
        quantities = request.args.getlist("units")
        date = str(datetime.datetime.utcnow())
        print(symbols)
        print(quantities)
        for i in range(len(symbols)):
            if int(quantities[i]) > 0:
                asset = db.execute("SELECT * FROM assets WHERE symbol = :symbol", {"symbol": symbols[i]}).fetchall()[0]
                db.execute("INSERT INTO investment (username, asset, buy_price, quantity, date) VALUES (:username, :asset, :buy_price, :quantity, :date)", {"username": username, "asset": asset.name, "buy_price": float(prices[i]), "quantity": int(quantities[i]), "date": date})
                print(f"Invested in {asset.name}")
        db.commit()
        db.close()
        return "<script>alert('All investments successful'); window.location = 'https://quantizers.herokuapp.com/';</script>"
    else:
        return "<script>alert('Method not allowed'); window.location = window.history.back();</script>"

def maximize_sharpe_ratio(annual_return, risk_free_rate, cov, k):
    srs = []
    portfolio_stds = []
    rand_wts = []
    portfolio_returns = []
    for i in range(0, 20000):
        random_weights = np.random.dirichlet(np.ones(k), size = 1).T
        rand_wts.append(random_weights)
        # portolfio return
        portfolio_return = np.sum(annual_return * random_weights)
        portfolio_returns.append(portfolio_return)
        # portfolio volatility
        portfolio_std = np.sqrt(np.dot(random_weights.T, np.dot(cov, random_weights))) * np.sqrt(252)
        portfolio_stds.append(portfolio_std)
        # sharpe ratio
        sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_std
        srs.append(sharpe_ratio)
    max_index = srs.index(max(srs))
    best_wts = rand_wts[max_index]
    #max_sr = srs[max_index]
    #portfolio_sd = portfolio_stds[max_index]
    #return_for_max_sr = portfolio_returns[max_index]

    return best_wts

def minimize_portfolio_variance(corr, stds, annual_return, k):
    port_vars = []
    rand_wts = []
    for i in range(0, 10000):
        random_weights = np.random.dirichlet(np.ones(k), size = 1).T
        rand_wts.append(random_weights)
        random_weighted_sd = stds * random_weights
        portfolio_var = np.sqrt(np.sum(np.dot(random_weighted_sd.T, np.dot(corr, random_weighted_sd))))*100
        port_vars.append(portfolio_var)
    min_index = port_vars.index(min(port_vars))
    best_wts = rand_wts[min_index]
    #min_var = port_vars[min_index]
    #return_for_min_pr = np.sum(annual_return * best_wts)

    return best_wts

def maximize_annual_return(e, stds, corr, annual_return, min_port_var, max_port_var, k):
    monthly = 0
    quarterly = 0
    half_yearly = 0
    yearly = 0
    # monthly
    start = "2016-04-01"
    for i in range(36):
        end = start[:5]
        month = int(start[5:7]) + 1
        if month <= 9:
            end += '0' + str(month) + start[7:]
        elif month > 12:
            end = str(int(start[:4]) + 1) + '-01-01'
        else:
            end += str(month) + start[7:]
        sliced_data = e.loc[(e.index >= start) & (e.index <= end)]
        monthly += (sliced_data.iloc[-1]/sliced_data.iloc[0] - 1)
        start = end
    # quarterly
    start = "2016-04-01"
    for i in range(12):
        end = start[:5]
        month = int(start[5:7]) + 3
        if month <= 9:
            end += '0' + str(month) + start[7:]
        elif month == 13:
            end = str(int(start[:4]) + 1) + '-01-01'
        else:
            end += str(month) + start[7:]
        sliced_data = e.loc[(e.index >= start) & (e.index <= end)]
        quarterly += (sliced_data.iloc[-1]/sliced_data.iloc[0] - 1)
        start = end
    # half-yearly
    start = "2016-04-01"
    for i in range(6):
        end = start[:5]
        month = int(start[5:7]) + 6
        if month == 16:
            end = str(int(start[:4]) + 1) + '-04-01'
        else:
            end += str(month) + start[7:]
        sliced_data = e.loc[(e.index >= start) & (e.index <= end)]
        half_yearly += (sliced_data.iloc[-1]/sliced_data.iloc[0] - 1)
        start = end
    # yearly
    start = "2016-04-01"
    for i in range(3):
        end = str(int(start[:4]) + 1) + start[4:]
        sliced_data = e.loc[(e.index >= start) & (e.index <= end)]
        yearly += (sliced_data.iloc[-1]/sliced_data.iloc[0] - 1)
        start = end

    avgs = [list(monthly*100/36), list(quarterly*100/12), list(half_yearly*100/6), list(yearly*100/3)]

    best_wts_for_avgs = []
    annual_returns_for_avgs = []
    port_vars_for_avgs = []
    for avg in avgs:
        port_vars = []
        returns = []
        rand_wts = []
        for i in range(0, 10000):
            random_weights = np.random.dirichlet(np.ones(k), size = 1).T
            random_weighted_sd = stds * random_weights
            portfolio_var = np.sqrt(np.sum(np.dot(random_weighted_sd.T, np.dot(corr, random_weighted_sd))))*100
            if (portfolio_var >= min_port_var) & (portfolio_var <= max_port_var):
                port_vars.append(portfolio_var)
                rand_wts.append(random_weights)
                total_return = np.sum(avg * random_weights.T)
                returns.append(total_return)
        max_index = returns.index(max(returns))
        max_return = returns[max_index]
        best_wts = rand_wts[max_index]
        #min_var = port_vars[max_index]

        best_wts_for_avgs.append(best_wts)
        #port_vars_for_avgs.append(min_var)
        annual_ret = np.sum(annual_return * best_wts)
        annual_returns_for_avgs.append(annual_ret)

    max_index = annual_returns_for_avgs.index(max(annual_returns_for_avgs))
    bestest_wts = best_wts_for_avgs[max_index]
    #maximum_return = annual_returns_for_avgs[max_index]
    #miniest_var = port_vars_for_avgs[max_index]

    return bestest_wts

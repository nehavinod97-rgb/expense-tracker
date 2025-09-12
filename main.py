import os
import sqlite3
from datetime import datetime
from flask import Flask, request, session, redirect, url_for, render_template, jsonify

app = Flask(__name__)
app.secret_key = "supersecret"

# Initialize DB
if not os.path.exists("database.db"):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT, password TEXT)")
    c.execute("CREATE TABLE expenses(id INTEGER PRIMARY KEY, user_id INTEGER, amount REAL, category TEXT, date TEXT)")
    conn.commit()
    conn.close()

def init_db():
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()    

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def get_db_connection():
    conn = sqlite3.connect("expenses.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()   # ✅ use database.db (with user_id)
    expenses = conn.execute("SELECT * FROM expenses WHERE user_id=?", (session["user"],)).fetchall()
    conn.close()

    expenses_list = [dict(expense) for expense in expenses]
    return render_template("dashboard.html", expenses=expenses_list)

@app.route("/home")
def homepage():
    if "user" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    expenses = conn.execute("SELECT * FROM expenses WHERE user_id=?", (session["user"],)).fetchall()
    return "This is home page"


@app.route("/api/expenses")
def api_expenses():
    if "user" in session:
        conn = get_db()
        expenses = conn.execute("SELECT * FROM expenses WHERE user_id=?", (session["user"],)).fetchall()
        return jsonify([dict(row) for row in expenses])
    return jsonify({"error": "Unauthorized"}), 401

@app.route("/delete/<int:expense_id>")
def delete_expense(expense_id):
    if "user" in session:
        conn = get_db()
        conn.execute("DELETE FROM expenses WHERE id=? AND user_id=?", (expense_id, session["user"]))
        conn.commit()
    return redirect(url_for("index"))


@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    if request.method == "POST":
        amount = request.form["amount"]
        category = request.form["category"]
        date = request.form["date"]
        conn.execute(
            "UPDATE expenses SET amount=?, category=?, date=? WHERE id=? AND user_id=?",
            (amount, category, date, expense_id, session["user"])
        )
        conn.commit()
        return redirect(url_for("index"))

    expense = conn.execute(
        "SELECT * FROM expenses WHERE id=? AND user_id=?", (expense_id, session["user"])
    ).fetchone()
    return render_template("edit.html", expense=expense)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (u,)).fetchone()
        if user and check_password_hash(user["password"], p):  # ✅ verify hash
            session["user"] = user["id"]
            return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        hashed_pw = generate_password_hash(p)  # ✅ secure hash

        conn = get_db()
        conn.execute("INSERT INTO users(username,password) VALUES(?,?)", (u, hashed_pw))
        conn.commit()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        conn = get_db()
        conn.execute("INSERT INTO users(username,password) VALUES(?,?)",(u,p))
        conn.commit()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.pop("user", None)  # remove user from session
    return redirect(url_for("login"))

@app.route("/add", methods=["POST"])
def add():
    if "user" in session:
        amount = request.form["amount"]
        category = request.form["category"]
        date_input = request.form["date"]

        # convert dd-mm-yyyy → yyyy-mm-dd
        try:
            date_obj = datetime.strptime(date_input, "%d-%m-%Y")
            date = date_obj.strftime("%Y-%m-%d")
        except:
            date = date_input  # fallback in case user enters directly

        conn = get_db()
        conn.execute("INSERT INTO expenses(user_id, amount, category, date) VALUES(?,?,?,?)",
                     (session["user"], amount, category, date))
        conn.commit()
    return redirect(url_for("index"))

if __name__ == "__main__":
        app.run(debug=True)



@app.route("/")
def home():
    return "Hello, Flask with Waitress!"

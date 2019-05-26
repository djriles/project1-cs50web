import os, requests, psycopg2, json
from flask import Flask, session, render_template, request, redirect, logging, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from passlib.hash import sha256_crypt

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["GET"])
def search():
    if not request.args.get("input"):
        return render_template("error.html", message="you must provide a book.")

    # Take input and add a wildcard
    input = "%" + request.args.get("input") + "%"

    # Capitalize all words of input for search
    # https://docs.python.org/3.7/library/stdtypes.html?highlight=title#str.title
    input = input.title()

    rows = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                        isbn LIKE :input OR \
                        title LIKE :input OR \
                        author LIKE :input LIMIT 15",
                        {"input": input})

    # Books not founded
    if rows.rowcount == 0:
        return render_template("error.html", message="we can't find books with that description.")
    # Fetch all the results
    books = rows.fetchall()
    #passing name as variable
    return render_template("results.html", books=books)


@app.route("/book/<string:isbn>", methods=["GET", "POST"])
def book(isbn):
    session["reviews"] = []
    user_name=session.get('user_name')

    secondreview = db.execute("SELECT * FROM reviews WHERE isbn=:isbn AND user_name=:user_name",{"user_name":user_name,"isbn":isbn}).fetchone()
    if request.method == "POST" and secondreview == None:
        comment = request.form.get("comment")
        rating = request.form.get("rating")
        db.execute("INSERT INTO reviews (isbn, review, rating, user_name) VALUES (:a,:b,:c,:d)",{"a":isbn,"b":comment,"c":rating,"d":user_name})
        db.commit()
    if request.method=="POST" and secondreview!=None:
        warning="Sorry. You cannot add second review."

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "8AxkJ7H3Zk1zWPKuO73r4A", "isbns": isbn})
    average_rating=res.json()['books'][0]['average_rating']
    work_ratings_count=res.json()['books'][0]['work_ratings_count']
    reviews=db.execute("SELECT * FROM reviews WHERE isbn = :isbn",{"isbn":isbn}).fetchall()
    for y in reviews:
        session['reviews'].append(y)
    books=db.execute("SELECT * FROM books WHERE isbn = :isbn",{"isbn":isbn}).fetchone()
    return render_template("book.html",books=books,reviews=session['reviews'],average_rating=average_rating,work_ratings_count=work_ratings_count,user_name=user_name)


@app.route("/api/<string:isbn>")
def api(isbn):
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn":isbn}).fetchone()
    if book==None:
        return render_template('error.html', message="No results")

    #python requests library (api)
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "8AxkJ7H3Zk1zWPKuO73r4A", "isbns": isbn})
    average_rating=res.json()['books'][0]['average_rating']
    work_ratings_count=res.json()['books'][0]['work_ratings_count']

    #create own API (JSON)
    book = {
    "title": book.title,
    "author": book.author,
    "year": book.year,
    "isbn": isbn,
    "review_count": work_ratings_count,
    "average_score": average_rating
    }

    x=json.dumps(book)
    return jsonify(x)


@app.route("/register.html", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user_name = request.form.get("user_name")
        user_password = request.form.get("user_password")
        confirm_user_password = request.form.get("confirm_user_password")
        secure_password = sha256_crypt.encrypt(str(user_password))

        if user_password == confirm_user_password:
            db.execute("INSERT INTO users(user_name, user_password) VALUES(:user_name, :user_password)", {"user_name": user_name, "user_password": secure_password})
            db.commit()
            return render_template("success.html", message = "Congrats! You've successfully registered.")
        else:
            return render_template("error.html", message = "Passwords don't match")

    return render_template("register.html")


@app.route("/login.html", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session['user_name'] = request.form['user_name']
        session['user_password'] = request.form['user_password']

        user_name_data = db.execute("SELECT user_name FROM users WHERE user_name=:user_name", {"user_name": session['user_name']}).fetchone()
        user_password_data = db.execute("SELECT user_password FROM users WHERE user_name=:user_name", {"user_name": session['user_name']}).fetchone()

        if user_name_data is None:
            return render_template("error.html", message="incorrect input")
        else:
            #check if password matches password in database
            for user in user_password_data:
                if sha256_crypt.verify(session['user_password'], user):
                    session["log"] = True
                    return render_template("index.html")
                else:
                    return render_template("error.html", message="wrong password")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.secret_key="12345asdfg"
    app.run(debug=True)

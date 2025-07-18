from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import users, db

# setting up defined paths as bluprint
auth_paths = Blueprint('auth', __name__)

# establish landing pad to throw user directly to registration page
@auth_paths.route('/')
def home():
    return redirect(url_for('auth.register'))

# setting up path for user to login to the page as user or admin (given an account alredy exists)
@auth_paths.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form["email"]
        passwd = request.form["pwd"]
        found_user = users.query.filter_by(email=email).first()
        if found_user and check_password_hash(found_user.passwd, passwd):
            session["email"] = email
            session["fname"] = found_user.fname
            return redirect(url_for('user.dashboard'))
        else:
            return render_template("login.html")
    else:
        if 'email' in session:
            return redirect(url_for('user.dashboard'))
        return render_template("login.html")

# setting up path for user to register to the site as a user
@auth_paths.route('/register', methods=['GET', 'POST'])
def register(): 
    if request.method == "POST":
        email = request.form["email"]
        passwd = request.form["pwd"]
        fname = request.form["fname"]
        addr = request.form["addr"]
        pcode = request.form["pcode"]

        found_user = users.query.filter_by(email=email).first()
        if not found_user:
            hashed_password = generate_password_hash(passwd)
            user_registry = users(email, hashed_password, fname, addr, pcode)
            db.session.add(user_registry)
            db.session.commit()

        session["email"] = email
        session["fname"] = fname
        return redirect(url_for('user.dashboard'))
    else:
        return render_template("register.html")

# setting up path so user can logout of the site and touch grass
@auth_paths.route('/logout')
def logout():
    session.pop("email", None)
    session.pop("fname", None)
    return redirect(url_for('auth.login'))
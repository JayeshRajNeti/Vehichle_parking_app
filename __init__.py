from flask import Flask, redirect, url_for, render_template, flash, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, users
app = Flask(__name__)
app.secret_key = 'xX_V3c50r_M@xxing_Xx'  # Set a secret key for session management

# Configure your database URI here if needed
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tables.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route('/')
def home():
    return redirect(url_for('register'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form["email"]
        passwd = request.form["pwd"]
        found_user = users.query.filter_by(email=email).first()
        if found_user and check_password_hash(found_user.passwd, passwd):
            session["email"] = email
            session["fname"] = found_user.fname
            return redirect(url_for('dashboard'))
        else:
            return render_template("login.html")
    else:
        if 'email' in session:
            return redirect(url_for('dashboard'))
        return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
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
        return redirect(url_for('dashboard'))
    else:
        return render_template("register.html")

@app.route('/dashboard')
def dashboard():
    if 'fname' in session:
        user = session['fname']
        if user == 'Admin':
            return redirect(url_for('admin'))
    else:
        return redirect(url_for('login'))
    return render_template('userdashboard.html', usrname=user)

@app.route('/admin')
def admin():
    if session['fname'] == 'Admin':
        user = session['fname']
    else:
        return redirect(url_for('login'))
    return render_template('admindashboard.html', usrname=user)
    

@app.route('/logout')
def logout():
    session.pop("email", None)
    session.pop("fname", None)
    return redirect(url_for('login'))
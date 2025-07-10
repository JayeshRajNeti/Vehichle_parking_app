from flask import Flask, redirect, url_for, render_template, flash, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, users, parkinglots, slots, reservations
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
    return render_template('user_dashboard.html', usrname=user)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if session.get('fname') != 'Admin':
        return redirect(url_for('login'))
    user = session['fname']
    search_query = request.args.get('search', '')
    if search_query:
        lots = parkinglots.query.filter(parkinglots.location.ilike(f'%{search_query}%')).all()
    else:
        lots = parkinglots.query.all()
    return render_template('admin_dashboard.html', usrname=user, parkinglots=lots, search_query=search_query)

@app.route('/admin/update_lot/<int:lotid>', methods=['GET', 'POST'])
def update_lot(lotid):
    if session.get('fname') != 'Admin':
        return redirect(url_for('login'))
    lot = parkinglots.query.get_or_404(lotid)
    if request.method == 'POST':
        lot.location = request.form['location']
        lot.address = request.form['address']
        lot.pincode = request.form['pincode']
        lot.price = int(request.form['price'])
        lot.spots = int(request.form['spots'])
        # db.session.commit() #Shift ahead later or ACID property will melt the damn project
        curr_slots = slots.query.filter_by(lotid = lotid).all()
        diff = lot.spots - len(curr_slots)
        print(f"slots to changed: {diff}")
        if diff > 0:
            for _ in range(diff):
                new_slot = slots(lot.lotid,None,None,False)
                db.session.add(new_slot)
                print("added slot")
                # db.session.flush()
                # print(f"slot {new_slot.slotid} added for {new_slot.slotid}: ")
        elif diff < 0:
            unoccupied_slots = [s for s in curr_slots if not s.occupied]
            if len(unoccupied_slots) >= abs(diff):
                for slot in unoccupied_slots[:abs(diff)]:
                    db.session.delete(slot)
            else:
                flash(f"Cannot reduce slots: only {len(unoccupied_slots)} unoccupied but need to remove {abs(diff)}", "danger")
                return redirect(url_for('update_lot', lotid=lotid))
        db.session.commit()
        flash('Parking lot updated successfully.')
        return redirect(url_for('admin'))
    return render_template('update_lot.html', lot=lot)

@app.route('/admin/delete_lot/<int:lotid>', methods=['POST'])
def delete_lot(lotid):
    if session.get('fname') != 'Admin':
        return redirect(url_for('login'))
    lot = parkinglots.query.get_or_404(lotid)
    slots_to_delete = slots.query.filter_by(lotid=lotid).all()
    for slot in slots_to_delete:
        db.session.delete(slot)
    db.session.delete(lot)
    db.session.commit()
    flash('Parking lot deleted successfully.')
    return redirect(url_for('admin'))

@app.route('/admin/create_lot', methods=['GET', 'POST'])
def create_lot():
    if session.get('fname') != 'Admin':
        return redirect(url_for('login'))
    if request.method == 'POST':
        location = request.form['location']
        address = request.form['address']
        pincode = request.form['pincode']
        price = int(request.form['price'])
        spots = int(request.form['spots'])
        new_lot = parkinglots(location, address, pincode, price, spots)
        db.session.add(new_lot)
        db.session.commit()
        for _ in range(spots):
            new_slot = slots(new_lot.lotid,None,None,False)
            db.session.add(new_slot)
            # db.session.flush()
            # print(f"slot {new_slot.slotid} added for {new_slot.slotid}: ")
        db.session.commit()
        flash('Parking lot created successfully.')
        return redirect(url_for('admin'))
    return render_template('create_lot.html')

@app.route('/logout')
def logout():
    session.pop("email", None)
    session.pop("fname", None)
    return redirect(url_for('login'))

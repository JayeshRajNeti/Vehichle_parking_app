from flask import Flask, redirect, url_for, render_template, flash, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, users, parkinglots, slots, reservations
from datetime import datetime

# setting up flask apps, keys and configs
app = Flask(__name__)
app.secret_key = 'xX_V3c50r_M@xxing_Xx'  
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tables.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# initialising the flask app
db.init_app(app)

# setting a default route when the user lands on the page, goes to reguster, duh
@app.route('/')
def home():
    return redirect(url_for('register'))

# login if the user already has an account
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

# registeration page link, take input, hash, store
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

# poor man's dashboard, no admin powers, book your cars, edit your details, reserve overpriced parking lots
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'fname' not in session:
        return redirect(url_for('login'))
    user_email = session['email']
    user = users.query.filter_by(email=user_email).first()
    if not user:
        return redirect(url_for('login'))
    if user.isadmin:
        return redirect(url_for('admin'))

    search_query = request.args.get('search', '')

    user_reservations = reservations.query.filter_by(userid=user.id, reserve_end=None).all()
    user_reservations_details = []
    for res in user_reservations:
        slot = slots.query.get(res.slotid)
        lot = parkinglots.query.get(slot.lotid) if slot else None
        if slot and lot:
            user_reservations_details.append({
                'reservation_id': res.id,
                'lotid': lot.lotid,
                'location': lot.location,
                'address': lot.address,
                'pincode': lot.pincode,
                'price': lot.price,
                'slotid': slot.slotid,
                'vehiclenum': slot.vehiclenum
            })

    if search_query:
        available_lots = parkinglots.query.filter(parkinglots.location.ilike(f'%{search_query}%')).all()
    else:
        available_lots = parkinglots.query.all()

    lots_with_availability = []
    for lot in available_lots:
        unoccupied_slots = slots.query.filter_by(lotid=lot.lotid, occupied=False).all()
        if unoccupied_slots:
            lots_with_availability.append({
                'lotid': lot.lotid,
                'location': lot.location,
                'address': lot.address,
                'pincode': lot.pincode,
                'price': lot.price,
                'available_slots': len(unoccupied_slots)
            })
    return render_template('user_dashboard.html', usrname=user.fname, user=user, user_reservations=user_reservations_details, available_lots=lots_with_availability, search_query=search_query)

# editing profile of the user
@app.route('/dashboard/edit_profile/<int:id>', methods=['GET', 'POST'])
def edit_profile(id):
    if 'email' not in session:
        return redirect(url_for('login'))
    user = users.query.get_or_404(id)
    if request.method == 'POST':
        user.email = request.form["email"]
        new_password = request.form["pwd"]
        if new_password:
            user.passwd = generate_password_hash(new_password)
        user.fname = request.form["fname"]
        user.addr = request.form["addr"]
        user.pcode = request.form["pcode"]
        db.session.commit()
        return redirect(url_for("dashboard"))
    else:
        return render_template('edit_profile.html', user=user)

# booking a lot, adding a reservation with start time
@app.route('/book_lot', methods=['POST'])
def book_lot():
    if 'email' not in session:
        return redirect(url_for('login'))
    user_email = session['email']
    user = users.query.filter_by(email=user_email).first()
    if not user:
        return redirect(url_for('login'))

    lotid = request.form.get('lotid')
    vehiclenum = request.form.get('vehiclenum', '')

    if not lotid:
        flash('Lot ID is required to book a lot.', 'danger')
        return redirect(url_for('dashboard'))

    lot = parkinglots.query.get(lotid)
    if not lot:
        flash('Parking lot not found.', 'danger')
        return redirect(url_for('dashboard'))

    slot = slots.query.filter_by(lotid=lot.lotid, occupied=False).first()
    if not slot:
        flash('No available slots in this lot.', 'danger')
        return redirect(url_for('dashboard'))

    slot.occupied = True
    slot.userid = user.id
    slot.vehiclenum = vehiclenum

    new_reservation = reservations(slot.slotid, user.id, datetime.now())
    db.session.add(new_reservation)
    db.session.commit()

    flash('Lot booked successfully.', 'success')
    return redirect(url_for('dashboard'))

# freeing a slot, adds the end time for a reservation too, finalising the entry
@app.route('/release_reservation', methods=['POST'])
def release_reservation():
    if 'email' not in session:
        return redirect(url_for('login'))
    user_email = session['email']
    user = users.query.filter_by(email=user_email).first()
    if not user:
        return redirect(url_for('login'))

    reservation_id = request.form.get('reservation_id')
    if not reservation_id:
        flash('Reservation ID is required to release a reservation.', 'danger')
        return redirect(url_for('dashboard'))

    reservation = reservations.query.get(reservation_id)
    if not reservation or reservation.userid != user.id or reservation.reserve_end is not None:
        flash('Invalid reservation.', 'danger')
        return redirect(url_for('dashboard'))

    reservation.reserve_end = datetime.now()

    slot = slots.query.get(reservation.slotid)
    if slot:
        slot.occupied = False
        slot.userid = None
        slot.vehiclenum = None

    db.session.commit()
    flash('Reservation released successfully.', 'success')
    return redirect(url_for('dashboard'))

# rich man's (admin's) dashboard, creates lots, edits lot protperties, sees all pesants and sees how much money they are burning
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

# updating a parking lot's data (finally, inflation in parking lot prices!)
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
        # db.session.commit() #Shift ahead later or ACID property will melt the project
        curr_slots = slots.query.filter_by(lotid = lotid).all()
        diff = lot.spots - len(curr_slots)
        print(f"slots to changed: {diff}")
        if diff > 0:
            for _ in range(diff):
                new_slot = slots(lot.lotid,None,None,False)
                db.session.add(new_slot)
                print("added slot")
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

# removes parking lots from existance
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

# brings parking lots to existance
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
        db.session.commit()
        flash('Parking lot created successfully.')
        return redirect(url_for('admin'))
    return render_template('create_lot.html')

# let's user logout and touch grass
@app.route('/logout')
def logout():
    session.pop("email", None)
    session.pop("fname", None)
    return redirect(url_for('login'))

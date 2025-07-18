from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from models import users, reservations, parkinglots, slots, db, func
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# setting up defined paths as blueprints
user_paths = Blueprint('user', __name__, url_prefix='')

# setting up user dashboard
@user_paths.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'fname' not in session:
        return redirect(url_for('auth.login'))
    user_email = session['email']
    user = users.query.filter_by(email=user_email).first()
    if not user:
        return redirect(url_for('auth.login'))
    if user.isadmin:
        return redirect(url_for('admin.admin_dashboard'))

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

# setting up path for user to edit his profile
@user_paths.route('/dashboard/edit_profile/<int:id>', methods=['GET', 'POST'])
def edit_profile(id):
    if 'email' not in session:
        return redirect(url_for('auth.login'))
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
        return redirect(url_for("user.dashboard"))
    else:
        return render_template('edit_profile.html', user=user)

# setting up path for user to book a lot with a vehicle num. (automatically adds an entry in reservation)
@user_paths.route('/book_lot', methods=['POST'])
def book_lot():
    if 'email' not in session:
        return redirect(url_for('auth.login'))
    user_email = session['email']
    user = users.query.filter_by(email=user_email).first()
    if not user:
        return redirect(url_for('auth.login'))

    lotid = request.form.get('lotid')
    vehiclenum = request.form.get('vehiclenum', '')

    if not lotid:
        flash('Lot ID is required to book a lot.', 'danger')
        return redirect(url_for('user.dashboard'))

    lot = parkinglots.query.get(lotid)
    if not lot:
        flash('Parking lot not found.', 'danger')
        return redirect(url_for('user.dashboard'))

    slot = slots.query.filter_by(lotid=lot.lotid, occupied=False).first()
    if not slot:
        flash('No available slots in this lot.', 'danger')
        return redirect(url_for('user.dashboard'))

    slot.occupied = True
    slot.userid = user.id
    slot.vehiclenum = vehiclenum

    new_reservation = reservations(slot.slotid, user.id, datetime.now())
    db.session.add(new_reservation)
    db.session.commit()

    flash('Lot booked successfully.', 'success')
    return redirect(url_for('user.dashboard'))

# setting up path for user to release a reservation (automatically adds the release time on reservations)
@user_paths.route('/release_reservation', methods=['POST'])
def release_reservation():
    if 'email' not in session:
        return redirect(url_for('auth.login'))
    user_email = session['email']
    user = users.query.filter_by(email=user_email).first()
    if not user:
        return redirect(url_for('auth.login'))

    reservation_id = request.form.get('reservation_id')
    if not reservation_id:
        flash('Reservation ID is required.', 'danger')
        return redirect(url_for('user.dashboard'))

    reservation = reservations.query.get(reservation_id)
    if not reservation or reservation.userid != user.id or reservation.reserve_end is not None:
        flash('Invalid reservation.', 'danger')
        return redirect(url_for('user.dashboard'))

    reservation.reserve_end = datetime.now()

    slot = slots.query.get(reservation.slotid)
    if slot:
        slot.occupied = False
        slot.userid = None
        slot.vehiclenum = None

    db.session.commit()
    flash('Reservation released.', 'success')
    return redirect(url_for('user.dashboard'))

# setting up the path for user to see his spending on parking lots and regret
@user_paths.route('/summary/<int:id>',methods = ['GET','POST'])
def user_summary(id):
    if 'email' not in session:
        return redirect(url_for('auth.login'))
    user_spending = (
        db.session.query(
            parkinglots.location,
            (parkinglots.price * func.count(slots.lotid)).label('total_price')
        )
        .join(slots, slots.lotid == parkinglots.lotid)
        .filter(slots.userid == id)
        .group_by(parkinglots.lotid, parkinglots.price)
        .all()
    )
    print(user_spending)
    return render_template('user_summary.html', user_spending=user_spending)

    

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import parkinglots, users , slots, db, func

# setting up defined paths as bluprint
admin_paths = Blueprint('admin', __name__, url_prefix='/admin')

# setting up admin dashboard
@admin_paths.route('/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if session.get('fname') != 'Admin':
        return redirect(url_for('auth.login'))
    user = session['fname']
    search_query = request.args.get('search', '')
    if search_query:
        lots = parkinglots.query.filter(parkinglots.location.ilike(f'%{search_query}%')).all()
    else:
        lots = parkinglots.query.all()
    return render_template('admin_dashboard.html', usrname=user, parkinglots=lots, search_query=search_query)

# setting up path for updating lot data
@admin_paths.route('/update_lot/<int:lotid>', methods=['GET', 'POST'])
def update_lot(lotid):
    if session.get('fname') != 'Admin':
        return redirect(url_for('auth.login'))
    lot = parkinglots.query.get_or_404(lotid)
    if request.method == 'POST':
        lot.location = request.form['location']
        lot.address = request.form['address']
        lot.pincode = request.form['pincode']
        lot.price = int(request.form['price'])
        lot.spots = int(request.form['spots'])

        curr_slots = slots.query.filter_by(lotid=lotid).all()
        diff = lot.spots - len(curr_slots)
        if diff > 0:
            for _ in range(diff):
                db.session.add(slots(lot.lotid, None, None, False))
        elif diff < 0:
            unoccupied = [s for s in curr_slots if not s.occupied]
            if len(unoccupied) >= abs(diff):
                for s in unoccupied[:abs(diff)]:
                    db.session.delete(s)
            else:
                flash("Not enough free slots to reduce", "danger")
                return redirect(url_for('admin.update_lot', lotid=lotid))

        db.session.commit()
        flash('Lot updated.', 'success')
        return redirect(url_for('admin.admin_dashboard'))
    return render_template('update_lot.html', lot=lot)

# setting up path so admin can delete a lot
@admin_paths.route('/delete_lot/<int:lotid>', methods=['POST'])
def delete_lot(lotid):
    if session.get('fname') != 'Admin':
        return redirect(url_for('auth.login'))
    lot = parkinglots.query.get_or_404(lotid)
    for s in slots.query.filter_by(lotid=lotid).all():
        db.session.delete(s)
    db.session.delete(lot)
    db.session.commit()
    flash('Lot deleted.')
    return redirect(url_for('admin.admin_dashboard'))

# setting up path for admin to create a lot
@admin_paths.route('/create_lot', methods=['GET', 'POST'])
def create_lot():
    if session.get('fname') != 'Admin':
        return redirect(url_for('auth.login'))
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
            db.session.add(slots(new_lot.lotid, None, None, False))
        db.session.commit()
        flash('Lot created.')
        return redirect(url_for('admin.admin_dashboard'))
    return render_template('create_lot.html')

# setting up path for admin to see all users and their data (except the password obviously)
@admin_paths.route('/userview', methods=['GET','POST'])
def admin_userview():
    if session.get('fname') != 'Admin':
        return redirect(url_for('auth.login'))
    search_query = request.args.get('search', '')
    if search_query:
        all_users = users.query.filter(users.fname.ilike(f'%{search_query}%')).all()
    else:
        all_users = users.query.all()
    return render_template('admin_userview.html', all_users=all_users, search_query=search_query)

# setting up the path for the admin to view the summary graphs for parking lot data
@admin_paths.route('/summary', methods=['GET','POST'])
def admin_summary():
    if session.get('fname') != 'Admin':
        return redirect(url_for('auth.login'))
    lot_profits = (
        db.session.query(
            parkinglots.location,
            (parkinglots.price * func.count(slots.lotid)).label('total_price')
        )
        .join(slots, slots.lotid == parkinglots.lotid)
        .filter(slots.occupied == True)
        .group_by(parkinglots.lotid, parkinglots.price)
        .all()
    )
    slots_used = (
        db.session.query(
            slots.occupied,   
            func.count(slots.occupied).label('count')
        )
        .group_by(slots.occupied)
        .all()
    )
    occupied_dist = (
        db.session.query(
            parkinglots.location,
            func.count(slots.occupied).label('weightage')
        )
        .join(slots, slots.lotid == parkinglots.lotid)
        .filter(slots.occupied == True)
        .group_by(parkinglots.location)
        .all()
    )
    return render_template('admin_summary.html', lot_profits=lot_profits, slots_used=slots_used, occupied_dist=occupied_dist)

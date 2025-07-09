from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    passwd = db.Column(db.String(120), nullable=False)
    fname = db.Column(db.String(120))
    addr = db.Column(db.String(255))
    pcode = db.Column(db.String(20))
    isadmin = db.Column(db.Boolean, default = False)
    reservations = db.relationship('reservations', backref='user', lazy=True)

    def __init__(self,email,passwd,fname,addr,pcode,isadmin=False):
        self.email = email
        self.passwd = passwd
        self.fname = fname
        self.addr = addr
        self.pcode = pcode
        self.isadmin = isadmin

class parkinglots(db.Model):
    lotid = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(255), unique=True, nullable=False)
    pincode = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    spots = db.Column(db.Integer, nullable=False)
    slots = db.relationship('slots', backref='lot', lazy=True)
    
    def __init__(self, location, address, pincode, price, spots):
        self.location = location
        self.address = address
        self.pincode = pincode
        self.price = price
        self.spots = spots

class slots(db.Model):
    slotid = db.Column(db.Integer, primary_key=True)
    lotid = db.Column(db.Integer, db.ForeignKey('parkinglots.lotid'),nullable=False)
    userid = db.Column(db.Integer, db.ForeignKey('users.id'))
    occupied = db.Column(db.Boolean, default = False)
    reservations = db.relationship('reservations', backref='slot', lazy=True)

    def __init__(self, slotid, lotid, userid, occupied):
        self.slotid = slotid
        self.lotid = lotid
        self.userid = userid
        self.occupied = occupied

class reservations(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slotid = db.Column(db.Integer, db.ForeignKey('slots.slotid'), nullable=False)
    userid = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reserve_start = db.Column(db.DateTime, nullable=False)
    reserve_end = db.Column(db.DateTime)

    def __init__(self, slotid, userid, reserve_start, reserve_end=None):
        self.slotid = slotid
        self.userid = userid
        self.reserve_start = reserve_start
        self.reserve_end = reserve_end        
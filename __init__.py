from flask import Flask
from models import db, users, parkinglots, slots, reservations
from controllers.admin_controller import admin_paths
from controllers.user_controller import user_paths
from controllers.auth_controller import auth_paths


# setting up flask apps, keys and configs
app = Flask(__name__)
app.secret_key = 'xX_V3c50r_M@xxing_Xx'  
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tables.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# initialising the flask app
db.init_app(app)

# register blueprints from controllers
app.register_blueprint(auth_paths)
app.register_blueprint(user_paths)
app.register_blueprint(admin_paths)


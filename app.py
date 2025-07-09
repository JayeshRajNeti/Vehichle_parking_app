from __init__ import app,db,users
from werkzeug.security import generate_password_hash, check_password_hash
if __name__ == '__main__':
    with app.app_context():
        print("Creating the database...")
        db.create_all()
        admin_query = users.query.filter_by(fname = "Admin", email = "admin@mail.com").first()
        if not admin_query:
            admin_registry = users("admin@mail.com",generate_password_hash("adminpass123"),"Admin",None,None,True)
            db.session.add(admin_registry)
            db.session.commit()
    app.run()

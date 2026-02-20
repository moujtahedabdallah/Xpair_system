from .database import db
from werkzeug.security import generate_password_hash, check_password_hash

class Person(db.Model):
    __tablename__ = 'person'

    # Variables
    id = db.Column(db.Integer, primary_key=True) 
    password = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    role = db.Column(db.String(20), default='customer')  # Role to support UC1 for all actors
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    
    # Methods
    def create_profile(self): 
        db.session.add(self) 
        db.session.commit() # This basically saves into the database

    def update_password(self, new_password):
        # Updates user's password
        self.password = new_password
        db.session.commit() # This basically saves into the database

    def update_first_name(self, new_first_name):
        # Updates user's first name
        self.first_name = new_first_name
        db.session.commit()

    def update_last_name(self, new_last_name):
        # Updates user's last name
        self.last_name = new_last_name
        db.session.commit()

    def update_email(self, new_email):
        # Updates user's email address
        self.email = new_email
        db.session.commit()
        
    def update_phone(self, new_phone):
        # Updates user's phone number
        self.phone = new_phone
        db.session.commit()

    def update_address(self, new_address):
        # Updates user's address
        self.address = new_address
        db.session.commit()
    
    def set_password(self, password):
        # Hashes the password and stores it securely
        self.password = generate_password_hash(password)

    def authenticate_user(self, inputted_password):
        # Checks if the provided password matches the stored hashed password
        return check_password_hash(self.password, inputted_password)




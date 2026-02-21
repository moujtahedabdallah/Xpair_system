from .database import db

class Vehicle(db.Model):
    __tablename__ = 'vehicle'

    # Variables
    vehicleID = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    plate = db.Column(db.String(20), unique=True, nullable=False)
    size = db.Column(db.String(20))
    type = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    
    #Foreign Key
    customerID = db.Column(db.Integer, db.ForeignKey('customer.customerID'), nullable=False)

    # Relationships for SQLAlchemy
    owner = db.relationship('Customer', backref='vehicles')

    # Methods
    def add_info(self):
        # Saves the new vehicle to the database
        db.session.add(self)
        db.session.commit()

    def update_make(self, new_make):
        # Updates vehicle make
        self.make = new_make
        db.session.commit()

    def update_model(self, new_model):
        # Updates vehicle model
        self.model = new_model
        db.session.commit()

    def update_year(self, new_year):
        # Updates vehicle year
        self.year = new_year
        db.session.commit()

    def update_plate(self, new_plate):
        # Updates vehicle plate
        self.plate = new_plate
        db.session.commit()

    def update_size(self, new_size):
        # Updates vehicle size
        self.size = new_size
        db.session.commit()

    def update_type(self, new_type):
        # Updates vehicle type
        self.type = new_type
        db.session.commit()
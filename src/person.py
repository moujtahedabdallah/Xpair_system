from .database import db

class Person(db.Model):
    __tablename__ = 'person'
    
    # This is the line the error is complaining about 
    id = db.Column(db.Integer, primary_key=True) 
    
    # Attributes from your Class Diagram [cite: 56-62]
    password = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    
    # Role to support UC1 for all actors
    role = db.Column(db.String(20), default='customer')
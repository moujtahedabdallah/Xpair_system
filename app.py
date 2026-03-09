from flask import Flask
from dotenv import load_dotenv
import os
from src.database import db
from src.person import Person
from src.vehicle import Vehicle
from src.service import Service
from src.booking import Booking
from src.availability_record import AvailabilityRecord
from src.customer import Customer
from src.employee import Employee
from src.manager import Manager
from flask_mail import Mail

load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///xpair_detailing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

mail = Mail()
db.init_app(app)
mail.init_app(app)

with app.app_context():
    try:
        db.create_all()
        print("✅ SUCCESS: All models are linked to SQLite!")
    except Exception as e:
        print(f"❌ ERROR: Something went wrong: {e}")

@app.route('/')
def home():
    return "<h1>Welcome to Xpair Detailing</h1>"

if __name__ == "__main__":
    app.run(debug=True)

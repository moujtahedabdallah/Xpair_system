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

mail = Mail() # added this because I had an error for mail.init_app(app)

# This handles the 'postgres' vs 'postgresql' naming issue automatically
uri = os.getenv('DATABASE_URL')
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    try:
        db.create_all()
        print(f"✅ SUCCESS: All models are linked to Postgres!")
    except Exception as e:
        print(f"❌ ERROR: Something went wrong: {e}")

@app.route('/')
def home():
    print("Route hit!")
    return "<h1>Welcome to Xpair Detailing</h1>"

if __name__ == "__main__":
    app.run(debug=True)

# Email configuration for Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

mail.init_app(app)

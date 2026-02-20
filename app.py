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

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
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
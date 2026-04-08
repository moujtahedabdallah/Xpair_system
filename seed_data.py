from src.database import db
from src.person import Person
from src.vehicle import Vehicle
from src.service import Service
from src.booking import Booking
from src.availability_record import AvailabilityRecord
from src.customer import Customer
from src.employee import Employee
from src.manager import Manager
from datetime import datetime
from flask import Flask
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///xpair_detailing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


def seed_data():
    with app.app_context():
        db.create_all()
        print("✅ SUCCESS: Database linked and tables created!")

        # 1. Add Test Manager
        if not Manager.query.filter_by(email="johnsnow@xpair.com").first():
            admin = Manager(
                first_name="John",
                last_name="Snow",
                email="johnsnow@xpair.com",
                phone="514-000-3434",
                password=generate_password_hash("348password"),
                max_car_capacity=5
            )
            db.session.add(admin)
            print("Manager added.")

        # 2. Add Service Catalog
        if not Service.query.first():
            for name in Service.SERVICE_DATA.keys():
                new_service = Service()
                new_service.apply_preset(name)
                db.session.add(new_service)
            print("Service catalog populated.")

        # 3. Add Test Customer, Vehicle, and Booking
        if not Customer.query.filter_by(email="test_customer@gmail.com").first():
            test_cust = Customer(
                first_name="John",
                last_name="Doe",
                email="test_customer@gmail.com",
                phone="450-555-9999",
                password=generate_password_hash("password123"),
            )
            db.session.add(test_cust)
            db.session.flush()

            test_car = Vehicle(
                make="Tesla",
                model="Model 3",
                year=2024,
                plate="XYZ224",
                size="medium",
                customerID=test_cust.customerID
            )
            db.session.add(test_car)
            db.session.flush()

            first_service = Service.query.first()
            if first_service:
                test_booking = Booking(
                    customerID=test_cust.customerID,
                    serviceID=first_service.serviceID,
                    vehicleID=test_car.vehicleID,
                    date=datetime(2026, 4, 7).date(),
                    start_time=datetime(2026, 4, 7, 9, 0),
                    end_time=datetime(2026, 4, 7, 10, 0),
                    booking_status='pending',
                    job_notes='Test booking - please detail carefully.'
                )
                db.session.add(test_booking)
                db.session.flush()
                print("Test customer, vehicle, and booking added.")

        # 4. Add Test Employee
        if not Employee.query.filter_by(email="test_employee@xpair.com").first():
            test_emp = Employee(
                first_name="Mike",
                last_name="Johnson",
                email="test_employee@xpair.com",
                phone="514-111-2222",
                password=generate_password_hash("password123"),
                role="employee",
                experience_level="junior",
                position="Detailer",
                salary=18.50,
                working_hours=40.0
            )
            db.session.add(test_emp)
            db.session.flush()
            print("Test employee added.")

            # 5. Add Test Availability Records
            records = [
                AvailabilityRecord(
                    employeeID=test_emp.employeeID,
                    periodID=1,
                    day="Monday",
                    start_time=datetime(2026, 4, 7, 9, 0),
                    end_time=datetime(2026, 4, 7, 17, 0),
                    status="pending"
                ),
                AvailabilityRecord(
                    employeeID=test_emp.employeeID,
                    periodID=1,
                    day="Wednesday",
                    start_time=datetime(2026, 4, 9, 9, 0),
                    end_time=datetime(2026, 4, 9, 17, 0),
                    status="pending"
                ),
                AvailabilityRecord(
                    employeeID=test_emp.employeeID,
                    periodID=1,
                    day="Friday",
                    start_time=datetime(2026, 4, 11, 12, 0),
                    end_time=datetime(2026, 4, 11, 18, 0),
                    status="approved"
                ),
            ]
            for r in records:
                db.session.add(r)
            print("Availability records added.")

            # 6. Assign existing booking to employee
            booking = Booking.query.first()
            if booking:
                booking.assigned_employee = test_emp.employeeID
                print("Booking assigned to employee.")

        db.session.commit()
        print("\nEVERYTHING IS READY! Your local SQLite database is populated.")


if __name__ == "__main__":
    seed_data()

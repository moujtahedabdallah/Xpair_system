from app import app
from src.database import db
from src.customer import Customer
from src.vehicle import Vehicle
from src.service import Service
from src.manager import Manager
from datetime import datetime

# This is just a seed file to test if populating the database works.
def seed_data():
    with app.app_context():

        # 1. Creates Manager
        if not Manager.query.filter_by(email="johnsnow@gmail.com").first():
            admin = Manager(
                # Checks if manager with this email already exists
                first_name="John",
                last_name="Snow",
                email="johnsnow@gmail.com",
                phone="514-000-3434",
                password="348password",
                max_car_capacity=5
            )
            db.session.add(admin)
            print("Manager added.")

        # 2. Add the Xpair Service Catalog
        if not Service.query.first():
            for name in Service.SERVICE_DATA.keys():
                new_service = Service()
                new_service.apply_preset(name)
                db.session.add(new_service)
            print("Service catalog populated.")

        # 3. Add a Test Customer and Vehicle
        if not Customer.query.filter_by(email="test_customer@gmail.com").first():
            # Checks if customer with this email already exists
            test_cust = Customer(
                first_name="John",
                last_name="Doe",
                email="test_customer@gmail.com",
                phone="450-555-9999",
                password="password123"
            )
            db.session.add(test_cust)
            db.session.flush() # Get the ID for the vehicle

            test_car = Vehicle(
                make="Tesla",
                model="Model 3",
                year=2024,
                plate="XYZ224",
                size="medium",
                customerID=test_cust.customerID
            )
            db.session.add(test_car)
            print("Test customer and vehicle added.")

        db.session.commit()
        print("\nEVERYTHING IS READY! Check your Neon dashboard now.")

if __name__ == "__main__":
    seed_data()
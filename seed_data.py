from src.database import db
from src.person import Person
from src.vehicle import Vehicle
from src.service import Service
from src.booking import Booking
from src.availability_record import AvailabilityRecord
from src.scheduling_period import SchedulingPeriod
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

        # ----------------------------------------------------------------
        # 1. MANAGER
        # ----------------------------------------------------------------
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

        # ----------------------------------------------------------------
        # 2. SCHEDULING PERIODS (UC6)
        # ----------------------------------------------------------------
        if not SchedulingPeriod.query.first():
            from datetime import date
            manager = Manager.query.filter_by(email="johnsnow@xpair.com").first()
            periods = [
                SchedulingPeriod(
                    label="March 31 - April 13, 2026",
                    start_date=date(2026, 3, 31), end_date=date(2026, 4, 13),
                    due_date=date(2026, 3, 28), status="closed",
                    created_by=manager.managerID if manager else None,
                ),
                SchedulingPeriod(
                    label="April 14 - 27, 2026",
                    start_date=date(2026, 4, 14), end_date=date(2026, 4, 27),
                    due_date=date(2026, 4, 9), status="open",
                    created_by=manager.managerID if manager else None,
                ),
                SchedulingPeriod(
                    label="April 28 - May 11, 2026",
                    start_date=date(2026, 4, 28), end_date=date(2026, 5, 11),
                    due_date=date(2026, 4, 23), status="upcoming",
                    created_by=manager.managerID if manager else None,
                ),
            ]
            for p in periods:
                db.session.add(p)
            db.session.flush()
            print("Scheduling periods seeded.")

        # ----------------------------------------------------------------
        # 3. SERVICE CATALOG
        # ----------------------------------------------------------------
        if not Service.query.first():
            for name in Service.SERVICE_DATA.keys():
                new_service = Service()
                new_service.apply_preset(name)
                db.session.add(new_service)
            print("Service catalog populated.")

        db.session.flush()

        # ----------------------------------------------------------------
        # 3. CUSTOMERS & VEHICLES
        # ----------------------------------------------------------------
        if not Customer.query.filter_by(email="test_customer@gmail.com").first():
            cust1 = Customer(
                first_name="John", last_name="Doe",
                email="test_customer@gmail.com", phone="450-555-9999",
                password=generate_password_hash("password123"),
            )
            db.session.add(cust1)
            db.session.flush()
            car1 = Vehicle(make="Tesla", model="Model 3", year=2024,
                           plate="XYZ224", size="medium", customerID=cust1.customerID)
            db.session.add(car1)
            db.session.flush()
            print("Customer 1 + vehicle added.")
        else:
            cust1 = Customer.query.filter_by(email="test_customer@gmail.com").first()
            car1  = Vehicle.query.filter_by(plate="XYZ224").first()

        if not Customer.query.filter_by(email="sarah.martin@gmail.com").first():
            cust2 = Customer(
                first_name="Sarah", last_name="Martin",
                email="sarah.martin@gmail.com", phone="514-222-3333",
                password=generate_password_hash("password123"),
            )
            db.session.add(cust2)
            db.session.flush()
            car2 = Vehicle(make="BMW", model="X5", year=2022,
                           plate="ABC987", size="large", customerID=cust2.customerID)
            db.session.add(car2)
            db.session.flush()
            print("Customer 2 + vehicle added.")
        else:
            cust2 = Customer.query.filter_by(email="sarah.martin@gmail.com").first()
            car2  = Vehicle.query.filter_by(plate="ABC987").first()

        if not Customer.query.filter_by(email="marc.leblanc@gmail.com").first():
            cust3 = Customer(
                first_name="Marc", last_name="Leblanc",
                email="marc.leblanc@gmail.com", phone="438-444-5555",
                password=generate_password_hash("password123"),
            )
            db.session.add(cust3)
            db.session.flush()
            car3 = Vehicle(make="Honda", model="Civic", year=2021,
                           plate="DEF456", size="small", customerID=cust3.customerID)
            db.session.add(car3)
            db.session.flush()
            print("Customer 3 + vehicle added.")
        else:
            cust3 = Customer.query.filter_by(email="marc.leblanc@gmail.com").first()
            car3  = Vehicle.query.filter_by(plate="DEF456").first()

        # ----------------------------------------------------------------
        # 4. EMPLOYEE
        # ----------------------------------------------------------------
        if not Employee.query.filter_by(email="test_employee@xpair.com").first():
            test_emp = Employee(
                first_name="Mike", last_name="Johnson",
                email="test_employee@xpair.com", phone="514-111-2222",
                password=generate_password_hash("password123"),
                role="employee", experience_level="junior",
                position="Detailer", salary=18.50, working_hours=40.0
            )
            db.session.add(test_emp)
            db.session.flush()
            print("Employee added.")

            # Availability records for UC6
            # periodID=1 → March 31 - April 13 (Submitted/approved)
            # periodID=2 → April 14 - 27 (Open — employee will submit via UC6)
            records = [
                # Period 1 — already submitted and approved (shows as Submitted on list)
                AvailabilityRecord(employeeID=test_emp.employeeID, periodID=1,
                    day="Tuesday", start_time=datetime(2026, 4, 1, 9, 0),
                    end_time=datetime(2026, 4, 1, 17, 0), status="approved"),
                AvailabilityRecord(employeeID=test_emp.employeeID, periodID=1,
                    day="Thursday", start_time=datetime(2026, 4, 3, 9, 0),
                    end_time=datetime(2026, 4, 3, 17, 0), status="approved"),
                AvailabilityRecord(employeeID=test_emp.employeeID, periodID=1,
                    day="Saturday", start_time=datetime(2026, 4, 5, 10, 0),
                    end_time=datetime(2026, 4, 5, 16, 0), status="approved"),
            ]
            for r in records:
                db.session.add(r)
            print("Availability records added (period 1 — approved).")
        else:
            test_emp = Employee.query.filter_by(email="test_employee@xpair.com").first()

        # ----------------------------------------------------------------
        # 5. BOOKINGS — full 6 months for dashboard bar chart
        #    Services: index 0=Basic($100), 1=Supreme($150), 2=Ultimate($200)
        # ----------------------------------------------------------------
        if Booking.query.count() == 0:
            services = Service.query.all()
            s0 = services[0]   # Basic Package          $100
            s1 = services[1]   # Xpair Supreme          $150
            s2 = services[2]   # Ultimate Exterior       $200

            bookings = [

                # ── NOVEMBER 2025 ──────────────────────────────────────
                Booking(customerID=cust1.customerID, serviceID=s0.serviceID,
                        vehicleID=car1.vehicleID, date=datetime(2025, 11, 4).date(),
                        start_time=datetime(2025, 11, 4, 9, 0),
                        end_time=datetime(2025, 11, 4, 10, 0),
                        booking_status="completed",
                        job_notes="Excellent finish on the Tesla."),

                Booking(customerID=cust2.customerID, serviceID=s1.serviceID,
                        vehicleID=car2.vehicleID, date=datetime(2025, 11, 12).date(),
                        start_time=datetime(2025, 11, 12, 10, 0),
                        end_time=datetime(2025, 11, 12, 13, 0),
                        booking_status="completed"),

                Booking(customerID=cust3.customerID, serviceID=s0.serviceID,
                        vehicleID=car3.vehicleID, date=datetime(2025, 11, 20).date(),
                        start_time=datetime(2025, 11, 20, 14, 0),
                        end_time=datetime(2025, 11, 20, 15, 0),
                        booking_status="cancelled"),

                Booking(customerID=cust1.customerID, serviceID=s2.serviceID,
                        vehicleID=car1.vehicleID, date=datetime(2025, 11, 27).date(),
                        start_time=datetime(2025, 11, 27, 9, 0),
                        end_time=datetime(2025, 11, 27, 13, 0),
                        booking_status="completed"),

                # ── DECEMBER 2025 ──────────────────────────────────────
                Booking(customerID=cust2.customerID, serviceID=s2.serviceID,
                        vehicleID=car2.vehicleID, date=datetime(2025, 12, 3).date(),
                        start_time=datetime(2025, 12, 3, 9, 0),
                        end_time=datetime(2025, 12, 3, 13, 0),
                        booking_status="completed"),

                Booking(customerID=cust3.customerID, serviceID=s1.serviceID,
                        vehicleID=car3.vehicleID, date=datetime(2025, 12, 10).date(),
                        start_time=datetime(2025, 12, 10, 11, 0),
                        end_time=datetime(2025, 12, 10, 14, 0),
                        booking_status="completed"),

                Booking(customerID=cust1.customerID, serviceID=s0.serviceID,
                        vehicleID=car1.vehicleID, date=datetime(2025, 12, 18).date(),
                        start_time=datetime(2025, 12, 18, 9, 0),
                        end_time=datetime(2025, 12, 18, 10, 0),
                        booking_status="completed"),

                Booking(customerID=cust2.customerID, serviceID=s1.serviceID,
                        vehicleID=car2.vehicleID, date=datetime(2025, 12, 23).date(),
                        start_time=datetime(2025, 12, 23, 13, 0),
                        end_time=datetime(2025, 12, 23, 16, 0),
                        booking_status="cancelled"),

                Booking(customerID=cust3.customerID, serviceID=s2.serviceID,
                        vehicleID=car3.vehicleID, date=datetime(2025, 12, 29).date(),
                        start_time=datetime(2025, 12, 29, 9, 0),
                        end_time=datetime(2025, 12, 29, 13, 0),
                        booking_status="completed"),

                # ── JANUARY 2026 ───────────────────────────────────────
                Booking(customerID=cust1.customerID, serviceID=s1.serviceID,
                        vehicleID=car1.vehicleID, date=datetime(2026, 1, 6).date(),
                        start_time=datetime(2026, 1, 6, 9, 0),
                        end_time=datetime(2026, 1, 6, 12, 0),
                        booking_status="completed"),

                Booking(customerID=cust2.customerID, serviceID=s0.serviceID,
                        vehicleID=car2.vehicleID, date=datetime(2026, 1, 13).date(),
                        start_time=datetime(2026, 1, 13, 10, 0),
                        end_time=datetime(2026, 1, 13, 11, 0),
                        booking_status="completed"),

                Booking(customerID=cust3.customerID, serviceID=s2.serviceID,
                        vehicleID=car3.vehicleID, date=datetime(2026, 1, 20).date(),
                        start_time=datetime(2026, 1, 20, 13, 0),
                        end_time=datetime(2026, 1, 20, 17, 0),
                        booking_status="completed"),

                Booking(customerID=cust1.customerID, serviceID=s0.serviceID,
                        vehicleID=car1.vehicleID, date=datetime(2026, 1, 27).date(),
                        start_time=datetime(2026, 1, 27, 9, 0),
                        end_time=datetime(2026, 1, 27, 10, 0),
                        booking_status="cancelled"),

                # ── FEBRUARY 2026 ──────────────────────────────────────
                Booking(customerID=cust2.customerID, serviceID=s2.serviceID,
                        vehicleID=car2.vehicleID, date=datetime(2026, 2, 4).date(),
                        start_time=datetime(2026, 2, 4, 9, 0),
                        end_time=datetime(2026, 2, 4, 13, 0),
                        booking_status="completed"),

                Booking(customerID=cust3.customerID, serviceID=s1.serviceID,
                        vehicleID=car3.vehicleID, date=datetime(2026, 2, 11).date(),
                        start_time=datetime(2026, 2, 11, 10, 0),
                        end_time=datetime(2026, 2, 11, 13, 0),
                        booking_status="completed"),

                Booking(customerID=cust1.customerID, serviceID=s0.serviceID,
                        vehicleID=car1.vehicleID, date=datetime(2026, 2, 18).date(),
                        start_time=datetime(2026, 2, 18, 14, 0),
                        end_time=datetime(2026, 2, 18, 15, 0),
                        booking_status="completed"),

                Booking(customerID=cust2.customerID, serviceID=s1.serviceID,
                        vehicleID=car2.vehicleID, date=datetime(2026, 2, 25).date(),
                        start_time=datetime(2026, 2, 25, 9, 0),
                        end_time=datetime(2026, 2, 25, 12, 0),
                        booking_status="completed"),

                # ── MARCH 2026 ─────────────────────────────────────────
                Booking(customerID=cust3.customerID, serviceID=s2.serviceID,
                        vehicleID=car3.vehicleID, date=datetime(2026, 3, 4).date(),
                        start_time=datetime(2026, 3, 4, 9, 0),
                        end_time=datetime(2026, 3, 4, 13, 0),
                        booking_status="completed"),

                Booking(customerID=cust1.customerID, serviceID=s1.serviceID,
                        vehicleID=car1.vehicleID, date=datetime(2026, 3, 10).date(),
                        start_time=datetime(2026, 3, 10, 10, 0),
                        end_time=datetime(2026, 3, 10, 13, 0),
                        booking_status="completed"),

                Booking(customerID=cust2.customerID, serviceID=s0.serviceID,
                        vehicleID=car2.vehicleID, date=datetime(2026, 3, 15).date(),
                        start_time=datetime(2026, 3, 15, 9, 0),
                        end_time=datetime(2026, 3, 15, 10, 0),
                        booking_status="cancelled"),

                Booking(customerID=cust3.customerID, serviceID=s0.serviceID,
                        vehicleID=car3.vehicleID, date=datetime(2026, 3, 19).date(),
                        start_time=datetime(2026, 3, 19, 11, 0),
                        end_time=datetime(2026, 3, 19, 12, 0),
                        booking_status="completed"),

                Booking(customerID=cust1.customerID, serviceID=s2.serviceID,
                        vehicleID=car1.vehicleID, date=datetime(2026, 3, 26).date(),
                        start_time=datetime(2026, 3, 26, 9, 0),
                        end_time=datetime(2026, 3, 26, 13, 0),
                        booking_status="completed"),

                # ── APRIL 2026 (current month) ─────────────────────────
                Booking(customerID=cust2.customerID, serviceID=s1.serviceID,
                        vehicleID=car2.vehicleID, date=datetime(2026, 4, 1).date(),
                        start_time=datetime(2026, 4, 1, 8, 0),
                        end_time=datetime(2026, 4, 1, 11, 0),
                        booking_status="completed"),

                Booking(customerID=cust3.customerID, serviceID=s2.serviceID,
                        vehicleID=car3.vehicleID, date=datetime(2026, 4, 3).date(),
                        start_time=datetime(2026, 4, 3, 13, 0),
                        end_time=datetime(2026, 4, 3, 17, 0),
                        booking_status="completed"),

                Booking(customerID=cust1.customerID, serviceID=s0.serviceID,
                        vehicleID=car1.vehicleID, date=datetime(2026, 4, 5).date(),
                        start_time=datetime(2026, 4, 5, 9, 0),
                        end_time=datetime(2026, 4, 5, 10, 0),
                        booking_status="completed",
                        job_notes="Customer requested extra attention on hood."),

                Booking(customerID=cust2.customerID, serviceID=s1.serviceID,
                        vehicleID=car2.vehicleID, date=datetime(2026, 4, 7).date(),
                        start_time=datetime(2026, 4, 7, 9, 0),
                        end_time=datetime(2026, 4, 7, 12, 0),
                        booking_status="in_progress",
                        job_notes="Test booking - please detail carefully."),

                Booking(customerID=cust3.customerID, serviceID=s0.serviceID,
                        vehicleID=car3.vehicleID, date=datetime(2026, 4, 8).date(),
                        start_time=datetime(2026, 4, 8, 10, 0),
                        end_time=datetime(2026, 4, 8, 11, 0),
                        booking_status="confirmed"),

                Booking(customerID=cust1.customerID, serviceID=s2.serviceID,
                        vehicleID=car1.vehicleID, date=datetime(2026, 4, 9).date(),
                        start_time=datetime(2026, 4, 9, 14, 0),
                        end_time=datetime(2026, 4, 9, 18, 0),
                        booking_status="pending"),
            ]

            for b in bookings:
                db.session.add(b)
            db.session.flush()

            # Assign some April bookings to employee so UC5 still works
            emp = Employee.query.filter_by(email="test_employee@xpair.com").first()
            if emp:
                for b in Booking.query.filter(
                    Booking.date >= datetime(2026, 4, 1).date()
                ).limit(3).all():
                    b.assigned_employee = emp.employeeID

            print(f"✅ {len(bookings)} bookings added across 6 months.")

        db.session.commit()
        print("\nEVERYTHING IS READY! Your local SQLite database is populated.")
        print("\nCredentials:")
        print("  Manager  → johnsnow@xpair.com     / 348password")
        print("  Employee → test_employee@xpair.com / password123")
        print("  Customer → test_customer@gmail.com / password123")


if __name__ == "__main__":
    seed_data()
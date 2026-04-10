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
from datetime import datetime, date
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
        # 1. MANAGERS
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
            db.session.flush()
            print("Manager 1 (John Snow) added.")
        else:
            admin = Manager.query.filter_by(email="johnsnow@xpair.com").first()

        if not Manager.query.filter_by(email="lisa.chen@xpair.com").first():
            admin2 = Manager(
                first_name="Lisa",
                last_name="Chen",
                email="lisa.chen@xpair.com",
                phone="514-000-5678",
                password=generate_password_hash("password123"),
                max_car_capacity=6
            )
            db.session.add(admin2)
            db.session.flush()
            print("Manager 2 (Lisa Chen) added.")

        db.session.flush()

        # ----------------------------------------------------------------
        # 2. SCHEDULING PERIODS
        # ----------------------------------------------------------------
        if not SchedulingPeriod.query.first():
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
            db.session.flush()
            print("Service catalog populated.")

        db.session.flush()

        # ----------------------------------------------------------------
        # 4. CUSTOMERS & VEHICLES
        # ----------------------------------------------------------------

        if not Customer.query.filter_by(email="test_customer@gmail.com").first():
            cust1 = Customer(
                first_name="John", last_name="Doe",
                email="test_customer@gmail.com", phone="450-555-9999",
                password=generate_password_hash("password123"),
                address="742 Evergreen Terrace, Montreal, QC H3Z 1A1",
            )
            db.session.add(cust1)
            db.session.flush()
            car1 = Vehicle(make="Tesla", model="Model 3", year=2024,
                           plate="XYZ224", size="medium", type="Car",
                           customerID=cust1.customerID)
            db.session.add(car1)
            db.session.flush()
            cust1.vehicle_id = car1.vehicleID
            print("Customer 1 (John Doe) + vehicle added.")
        else:
            cust1 = Customer.query.filter_by(email="test_customer@gmail.com").first()
            car1  = Vehicle.query.filter_by(plate="XYZ224").first()

        if not Customer.query.filter_by(email="sarah.martin@gmail.com").first():
            cust2 = Customer(
                first_name="Sarah", last_name="Martin",
                email="sarah.martin@gmail.com", phone="514-222-3333",
                password=generate_password_hash("password123"),
                address="221B Baker Street, Laval, QC H7N 2B3",
            )
            db.session.add(cust2)
            db.session.flush()
            car2 = Vehicle(make="BMW", model="X5", year=2022,
                           plate="ABC987", size="large", type="SUV",
                           customerID=cust2.customerID)
            db.session.add(car2)
            db.session.flush()
            cust2.vehicle_id = car2.vehicleID
            print("Customer 2 (Sarah Martin) + vehicle added.")
        else:
            cust2 = Customer.query.filter_by(email="sarah.martin@gmail.com").first()
            car2  = Vehicle.query.filter_by(plate="ABC987").first()

        if not Customer.query.filter_by(email="marc.leblanc@gmail.com").first():
            cust3 = Customer(
                first_name="Marc", last_name="Leblanc",
                email="marc.leblanc@gmail.com", phone="438-444-5555",
                password=generate_password_hash("password123"),
                address="55 Rue Saint-Denis, Montreal, QC H2X 3K5",
            )
            db.session.add(cust3)
            db.session.flush()
            car3 = Vehicle(make="Honda", model="Civic", year=2021,
                           plate="DEF456", size="small", type="Car",
                           customerID=cust3.customerID)
            db.session.add(car3)
            db.session.flush()
            cust3.vehicle_id = car3.vehicleID
            print("Customer 3 (Marc Leblanc) + vehicle added.")
        else:
            cust3 = Customer.query.filter_by(email="marc.leblanc@gmail.com").first()
            car3  = Vehicle.query.filter_by(plate="DEF456").first()

        if not Customer.query.filter_by(email="priya.sharma@gmail.com").first():
            cust4 = Customer(
                first_name="Priya", last_name="Sharma",
                email="priya.sharma@gmail.com", phone="514-888-1234",
                password=generate_password_hash("password123"),
                address="900 Boul. René-Lévesque, Montreal, QC H3B 4A5",
            )
            db.session.add(cust4)
            db.session.flush()
            car4 = Vehicle(make="Toyota", model="RAV4", year=2023,
                           plate="GHI789", size="medium", type="SUV",
                           customerID=cust4.customerID)
            db.session.add(car4)
            db.session.flush()
            cust4.vehicle_id = car4.vehicleID
            print("Customer 4 (Priya Sharma) + vehicle added.")
        else:
            cust4 = Customer.query.filter_by(email="priya.sharma@gmail.com").first()
            car4  = Vehicle.query.filter_by(plate="GHI789").first()

        db.session.flush()

        # ----------------------------------------------------------------
        # 5. EMPLOYEES
        # ----------------------------------------------------------------
        if not Employee.query.filter_by(email="test_employee@xpair.com").first():
            emp1 = Employee(
                first_name="Mike", last_name="Johnson",
                email="test_employee@xpair.com", phone="514-111-2222",
                password=generate_password_hash("password123"),
                role="employee", experience_level="junior",
                position="Detailer", salary=18.50, working_hours=40.0
            )
            db.session.add(emp1)
            db.session.flush()
            print("Employee 1 (Mike Johnson) added.")
        else:
            emp1 = Employee.query.filter_by(email="test_employee@xpair.com").first()

        if not Employee.query.filter_by(email="carlos.reyes@xpair.com").first():
            emp2 = Employee(
                first_name="Carlos", last_name="Reyes",
                email="carlos.reyes@xpair.com", phone="514-333-7777",
                password=generate_password_hash("password123"),
                role="employee", experience_level="senior",
                position="Lead Detailer", salary=24.00, working_hours=40.0
            )
            db.session.add(emp2)
            db.session.flush()
            print("Employee 2 (Carlos Reyes) added.")
        else:
            emp2 = Employee.query.filter_by(email="carlos.reyes@xpair.com").first()

        if not Employee.query.filter_by(email="aisha.dupont@xpair.com").first():
            emp3 = Employee(
                first_name="Aisha", last_name="Dupont",
                email="aisha.dupont@xpair.com", phone="514-777-9999",
                password=generate_password_hash("password123"),
                role="employee", experience_level="intermediate",
                position="Detailer", salary=21.00, working_hours=35.0
            )
            db.session.add(emp3)
            db.session.flush()
            print("Employee 3 (Aisha Dupont) added.")
        else:
            emp3 = Employee.query.filter_by(email="aisha.dupont@xpair.com").first()

        db.session.flush()

        # ----------------------------------------------------------------
        # 6. AVAILABILITY RECORDS
        #    Period 1 (closed) → all reviewed (approved + changes_requested)
        #    Period 2 (open)   → mix of pending so manager list is populated
        # ----------------------------------------------------------------
        if AvailabilityRecord.query.count() == 0:
            availability_records = [

                # ── PERIOD 1 (closed) — emp1: approved ──────────────────
                AvailabilityRecord(
                    employeeID=emp1.employeeID, periodID=1,
                    day="Tuesday",
                    start_time=datetime(2026, 4, 1, 9, 0),
                    end_time=datetime(2026, 4, 1, 17, 0),
                    status="approved",
                    manager_notes="Looks good.",
                    managerID=admin.managerID,
                ),
                AvailabilityRecord(
                    employeeID=emp1.employeeID, periodID=1,
                    day="Thursday",
                    start_time=datetime(2026, 4, 3, 9, 0),
                    end_time=datetime(2026, 4, 3, 17, 0),
                    status="approved",
                    managerID=admin.managerID,
                ),
                AvailabilityRecord(
                    employeeID=emp1.employeeID, periodID=1,
                    day="Saturday",
                    start_time=datetime(2026, 4, 5, 10, 0),
                    end_time=datetime(2026, 4, 5, 16, 0),
                    status="approved",
                    managerID=admin.managerID,
                ),

                # ── PERIOD 1 (closed) — emp2: changes_requested ─────────
                AvailabilityRecord(
                    employeeID=emp2.employeeID, periodID=1,
                    day="Monday",
                    start_time=datetime(2026, 3, 31, 8, 0),
                    end_time=datetime(2026, 3, 31, 14, 0),
                    status="changes_requested",
                    manager_notes="Please extend until 5 PM — we have a full booking that day.",
                    managerID=admin.managerID,
                ),
                AvailabilityRecord(
                    employeeID=emp2.employeeID, periodID=1,
                    day="Wednesday",
                    start_time=datetime(2026, 4, 2, 9, 0),
                    end_time=datetime(2026, 4, 2, 17, 0),
                    status="approved",
                    managerID=admin.managerID,
                ),

                # ── PERIOD 1 (closed) — emp3: approved ──────────────────
                AvailabilityRecord(
                    employeeID=emp3.employeeID, periodID=1,
                    day="Friday",
                    start_time=datetime(2026, 4, 4, 10, 0),
                    end_time=datetime(2026, 4, 4, 16, 0),
                    status="approved",
                    managerID=admin.managerID,
                ),

                # ── PERIOD 2 (open) — emp1: pending (just submitted) ────
                AvailabilityRecord(
                    employeeID=emp1.employeeID, periodID=2,
                    day="Tuesday",
                    start_time=datetime(2026, 4, 14, 9, 0),
                    end_time=datetime(2026, 4, 14, 17, 0),
                    status="pending",
                ),
                AvailabilityRecord(
                    employeeID=emp1.employeeID, periodID=2,
                    day="Thursday",
                    start_time=datetime(2026, 4, 16, 9, 0),
                    end_time=datetime(2026, 4, 16, 17, 0),
                    status="pending",
                ),
                AvailabilityRecord(
                    employeeID=emp1.employeeID, periodID=2,
                    day="Friday",
                    start_time=datetime(2026, 4, 17, 10, 0),
                    end_time=datetime(2026, 4, 17, 15, 0),
                    status="pending",
                ),

                # ── PERIOD 2 (open) — emp2: pending ─────────────────────
                AvailabilityRecord(
                    employeeID=emp2.employeeID, periodID=2,
                    day="Monday",
                    start_time=datetime(2026, 4, 14, 8, 0),
                    end_time=datetime(2026, 4, 14, 17, 0),
                    status="pending",
                ),
                AvailabilityRecord(
                    employeeID=emp2.employeeID, periodID=2,
                    day="Wednesday",
                    start_time=datetime(2026, 4, 16, 9, 0),
                    end_time=datetime(2026, 4, 16, 18, 0),
                    status="pending",
                ),

                # ── PERIOD 2 (open) — emp3: not yet submitted ────────────
                # (intentionally absent so the manager list shows one employee without a submission)
            ]

            for r in availability_records:
                db.session.add(r)
            db.session.flush()
            print(f"{len(availability_records)} availability records added.")

        # ----------------------------------------------------------------
        # 7. BOOKINGS — 6 months of history for dashboard + live statuses
        #    Services fetched by order: 0=Basic, 1=Supreme, 2=Ultimate Exterior
        # ----------------------------------------------------------------
        if Booking.query.count() == 0:
            services = Service.query.all()
            s0 = services[0]   # Basic Package              $100  60 min
            s1 = services[1]   # Xpair Supreme Package      $150 180 min
            s2 = services[2]   # Ultimate Xpair Exterior    $200 240 min
            s3 = services[3]   # Complete Engine Cleaning    $60  45 min

            # Customer home addresses for seeding realistic service locations
            ADDR = {
                cust1.customerID: "742 Evergreen Terrace, Montreal, QC H3Z 1A1",
                cust2.customerID: "221B Baker Street, Laval, QC H7N 2B3",
                cust3.customerID: "55 Rue Saint-Denis, Montreal, QC H2X 3K5",
                cust4.customerID: "900 Boul. René-Lévesque, Montreal, QC H3B 4A5",
            }

            # Helper: compact booking constructor
            def bk(cust, svc, veh, dt, status, emp=None, notes=None, addons=None, addr=None):
                start = datetime(*dt)
                end   = datetime(start.year, start.month, start.day,
                                 start.hour + svc.service_duration // 60,
                                 svc.service_duration % 60)
                b = Booking(
                    customerID=cust.customerID,
                    serviceID=svc.serviceID,
                    vehicleID=veh.vehicleID,
                    date=start.date(),
                    start_time=start,
                    end_time=end,
                    booking_status=status,
                    assigned_employee=emp.employeeID if emp else None,
                    job_notes=notes,
                    service_address=addr or ADDR.get(cust.customerID),
                )
                return b, addons

            raw_bookings = [

                # ── NOVEMBER 2025 ───────────────────────────────────────
                bk(cust1, s0, car1, (2025,11,4,9,0),   "completed", emp2, "Excellent finish on the Tesla."),
                bk(cust2, s1, car2, (2025,11,12,10,0), "completed", emp2),
                bk(cust3, s0, car3, (2025,11,20,14,0), "cancelled"),
                bk(cust1, s2, car1, (2025,11,27,9,0),  "completed", emp1),

                # ── DECEMBER 2025 ───────────────────────────────────────
                bk(cust2, s2, car2, (2025,12,3,9,0),   "completed", emp2),
                bk(cust3, s1, car3, (2025,12,10,11,0), "completed", emp1),
                bk(cust1, s0, car1, (2025,12,18,9,0),  "completed", emp2),
                bk(cust2, s1, car2, (2025,12,23,13,0), "cancelled"),
                bk(cust3, s2, car3, (2025,12,29,9,0),  "completed", emp1),

                # ── JANUARY 2026 ────────────────────────────────────────
                bk(cust1, s1, car1, (2026,1,6,9,0),    "completed", emp2),
                bk(cust2, s0, car2, (2026,1,13,10,0),  "completed", emp1),
                bk(cust3, s2, car3, (2026,1,20,13,0),  "completed", emp2),
                bk(cust4, s1, car4, (2026,1,22,9,0),   "completed", emp3, "New customer, first visit."),
                bk(cust1, s0, car1, (2026,1,27,9,0),   "cancelled"),

                # ── FEBRUARY 2026 ───────────────────────────────────────
                bk(cust2, s2, car2, (2026,2,4,9,0),    "completed", emp2),
                bk(cust3, s1, car3, (2026,2,11,10,0),  "completed", emp1),
                bk(cust4, s2, car4, (2026,2,14,9,0),   "completed", emp2, None, ["Leather Seat Conditioner", "Odor Neutralizer"]),
                bk(cust1, s0, car1, (2026,2,18,14,0),  "completed", emp3),
                bk(cust2, s1, car2, (2026,2,25,9,0),   "completed", emp1),

                # ── MARCH 2026 ──────────────────────────────────────────
                bk(cust3, s2, car3, (2026,3,4,9,0),    "completed", emp2),
                bk(cust4, s0, car4, (2026,3,7,10,0),   "completed", emp3),
                bk(cust1, s1, car1, (2026,3,10,10,0),  "completed", emp1),
                bk(cust2, s0, car2, (2026,3,15,9,0),   "cancelled"),
                bk(cust3, s0, car3, (2026,3,19,11,0),  "completed", emp2),
                bk(cust1, s2, car1, (2026,3,26,9,0),   "completed", emp1, None, ["UV Protection for Plastics", "Black Surface Restoration (Tires)"]),

                # ── APRIL 2026 — current month ───────────────────────────

                # Completed (past days)
                bk(cust2, s1, car2, (2026,4,1,8,0),   "completed", emp2),
                bk(cust3, s2, car3, (2026,4,3,13,0),  "completed", emp1),
                bk(cust4, s1, car4, (2026,4,4,9,0),   "completed", emp3, "Customer requested steam clean interior."),
                bk(cust1, s0, car1, (2026,4,5,9,0),   "completed", emp2, "Extra attention on hood."),
                bk(cust3, s3, car3, (2026,4,6,11,0),  "completed", emp1),

                # In progress (today's jobs — UC5 main demo)
                bk(cust2, s1, car2, (2026,4,9,9,0),   "in_progress", emp1, "Ceramic coating package — handle with care.", ["Xpair Detailing Air Freshener"]),
                bk(cust4, s2, car4, (2026,4,9,13,0),  "in_progress", emp2, "Customer wants extra polish on bumper."),

                # Confirmed (upcoming, assigned)
                bk(cust1, s2, car1, (2026,4,10,9,0),  "confirmed", emp1, None, ["Deep Carpet and Floor Cleaning", "Leather Seat Conditioner"]),
                bk(cust3, s0, car3, (2026,4,10,14,0), "confirmed", emp2),
                bk(cust4, s1, car4, (2026,4,11,10,0), "confirmed", emp3),

                # Pending (not yet assigned — tests manager assign flow)
                bk(cust2, s2, car2, (2026,4,12,9,0),  "pending"),
                bk(cust1, s0, car1, (2026,4,13,11,0), "pending"),
                bk(cust3, s2, car3, (2026,4,14,9,0),  "pending", None, "Guest noted a scratch on front bumper."),

                # Flagged / On Hold — tests manager dashboard alert + Modify Bookings flag UI
                bk(cust4, s1, car4, (2026,4,7,10,0),  "cancelled"),
            ]

            all_inserted = []
            for entry in raw_bookings:
                b_obj, addons = entry
                db.session.add(b_obj)
                db.session.flush()

                if b_obj.customer and b_obj.service and b_obj.vehicle:
                    b_obj.generate_booking_summary(selected_add_ons=addons if addons else None)

                all_inserted.append(b_obj)

            db.session.flush()

            # ── FLAGGED JOBS (on_hold) — tests dashboard alert + flag UI ──
            # Manually create so we can set block_reason and assigned employee
            flagged1 = Booking(
                customerID=cust2.customerID, serviceID=s1.serviceID,
                vehicleID=car2.vehicleID, date=datetime(2026, 4, 10).date(),
                start_time=datetime(2026, 4, 10, 9, 0),
                end_time=datetime(2026, 4, 10, 12, 0),
                booking_status='on_hold',
                is_blocked=False,
                assigned_employee=emp1.employeeID,
                block_reason="Customer was aggressive and refused access to the vehicle.",
                job_notes="Escalated to manager.",
                service_address=ADDR.get(cust2.customerID),
            )
            db.session.add(flagged1)
            db.session.flush()
            flagged1.generate_booking_summary()

            flagged2 = Booking(
                customerID=cust3.customerID, serviceID=s0.serviceID,
                vehicleID=car3.vehicleID, date=datetime(2026, 4, 11).date(),
                start_time=datetime(2026, 4, 11, 13, 0),
                end_time=datetime(2026, 4, 11, 14, 0),
                booking_status='on_hold',
                is_blocked=False,
                assigned_employee=emp2.employeeID,
                block_reason="Vehicle not accessible — customer parked in a no-entry zone.",
                service_address=ADDR.get(cust3.customerID),
            )
            db.session.add(flagged2)
            db.session.flush()
            flagged2.generate_booking_summary()

            print(f"✅ {len(all_inserted)} bookings + 2 flagged jobs added.")

            # ── CLOSURES (blocked time slots) ────────────────────────────
            manager = Manager.query.filter_by(email="johnsnow@xpair.com").first()
            if manager:
                manager.block_time_slot(
                    block_reason="Shop equipment maintenance — bay unavailable.",
                    start_time=datetime(2026, 4, 11, 8, 0),
                    end_time=datetime(2026, 4, 11, 12, 0),
                )
                manager.block_time_slot(
                    block_reason="Staff training session.",
                    start_time=datetime(2026, 4, 18, 9, 0),
                    end_time=datetime(2026, 4, 18, 17, 0),
                )
                manager.block_time_slot(
                    block_reason="Public holiday — shop closed.",
                    start_time=datetime(2026, 5, 18, 8, 0),
                    end_time=datetime(2026, 5, 18, 17, 0),
                )
                print("3 closures (blocked slots) added.")

        db.session.commit()

        print("\n" + "="*55)
        print("   EVERYTHING IS READY! Database is fully populated.")
        print("="*55)
        print("\nLogin Credentials:")
        print("  Manager  1 → johnsnow@xpair.com        / 348password")
        print("  Manager  2 → lisa.chen@xpair.com       / password123")
        print("  Employee 1 → test_employee@xpair.com   / password123  (Mike Johnson)")
        print("  Employee 2 → carlos.reyes@xpair.com    / password123  (Carlos Reyes)")
        print("  Employee 3 → aisha.dupont@xpair.com    / password123  (Aisha Dupont)")
        print("  Customer 1 → test_customer@gmail.com   / password123  (John Doe)")
        print("  Customer 2 → sarah.martin@gmail.com    / password123  (Sarah Martin)")
        print("  Customer 3 → marc.leblanc@gmail.com    / password123  (Marc Leblanc)")
        print("  Customer 4 → priya.sharma@gmail.com    / password123  (Priya Sharma)")
        print()
        print("Features covered:")
        print("  ✅ UC1  Auth — 2 managers, 3 employees, 4 customers seeded")
        print("  ✅ UC3  Booking — 6 months history, all statuses, add-ons, summaries, service addresses")
        print("  ✅ UC4  Availability submission — period 2 has pending records ready")
        print("  ✅ UC5  Employee jobs — in_progress/confirmed/completed assigned to each emp")
        print("  ✅ UC5  Flagged jobs — 2 on_hold jobs with reasons trigger dashboard alert")
        print("  ✅ UC6  Manager modify — pending bookings to assign/reschedule/cancel")
        print("  ✅ UC6  Closures — 3 blocked slots seeded (edit/remove testable)")
        print("  ✅ UC7  Availability review — approved, changes_requested, pending all present")
        print("  ✅ UC8  Dashboard — dense multi-month history + flagged jobs alert")


if __name__ == "__main__":
    seed_data()
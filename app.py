from flask import Flask
from src.database import db
from src.person import Person # Testing just the parent class for now

app = Flask(__name__)

# CONFIGURATION: Replace with your actual Postgres credentials
# Format: postgresql://username:password@localhost:5432/database_name
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:yourpassword@localhost:5432/xpair_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the 'General' hub with this specific app
db.init_app(app)

# THE TEST: This block tries to talk to Postgres and create the table
with app.app_context():
    try:
        db.create_all()
        print("✅ SUCCESS: The Person model is linked to Postgres!")
    except Exception as e:
        print(f"❌ ERROR: Something went wrong: {e}")

@app.route('/')
def home():
    return "<h1>Welcome to Xpair Detailing</h1><p>The system is live and the database is connected!</p>"

if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask
from dotenv import load_dotenv
import os
from src.database import db
from src.person import Person

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

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
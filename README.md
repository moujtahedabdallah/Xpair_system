# Xpair Detailing System
Python 3.12.12

## Overview
A web-based management system for Xpair Detailing, handling bookings, employee scheduling, availability, and customer notifications.

## Setup
Clone the repo, create a virtual environment, install required packages, then run the app.

git clone https://github.com/moujtahedabdallah/Xpair_system.git
cd Xpair_system

Mac/Linux:
python3 -m venv .venv
source .venv/bin/activate

Windows:
py -m venv .venv
.venv\Scripts\Activate.ps1

Install required packages:
python -m pip install --upgrade pip
pip install -r requirements.txt

Create a .env file in the project root:
MAIL_USERNAME=xpairdetailing@gmail.com
MAIL_PASSWORD=fgrd nwei fukv sdwi

Run the app:
python3 app.py

The database will be generated automatically on first run.
Access the website at: http://127.0.0.1:5000

## Project Structure
src is where .py files go
static is where .html files go
css is where .css files go
js is where javascript files go

## Git Workflow
When starting work: git pull
When finishing work: git add . → git commit -m "what you changed" → git push
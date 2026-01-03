🏥 MediFlow – Smart Hospital Queue Management System

MediFlow is a smart hospital queue management system designed to improve patient experience and optimize healthcare workflows.
It combines AI-driven queue prioritization with QR-based patient identification to streamline clinic operations and significantly reduce waiting times.

🚀 Features

✅ QR Code–based Patient Identification

🤖 AI Queue Management for fair and efficient patient prioritization

⏳ Estimated Waiting Time Prediction

📂 Instant Digital Patient Record Retrieval for doctors

❓ Frequently Asked Questions (FAQs) module for patients

📊 Improved transparency and reduced congestion in clinics

🛠 Tech Stack

Frontend: HTML, CSS, Bootstrap

Backend: Python (Flask)

Database: PostgreSQL (Hosted on Supabase)

Other Technologies:

QR Code Generation

AI Algorithm for Queue Prioritization

🌐 Hosted Application

🔗 Live Demo:
👉 https://medi-flow-g82j.onrender.com

⚠️ Note: Hosted version may have limited access depending on user roles (Admin / Doctor / Nurse / Patient).

📦 Running MediFlow Locally (Without Git)

This section is for supervisors or evaluators who receive the project as a ZIP or folder upload, not via GitHub.

1️⃣ Prerequisites

Make sure the following are installed:

Python 3.10+

pip (Python package manager)

Virtual Environment support (venv)

2️⃣ Extract Project Folder

Unzip the provided project folder

Open a terminal inside the project root directory

cd mediflow

3️⃣ Create & Activate Virtual Environment

Windows

python -m venv venv
venv\Scripts\activate


Mac / Linux

python3 -m venv venv
source venv/bin/activate

4️⃣ Install Required Dependencies
pip install -r requirements.txt

5️⃣ Configure Environment Variables

Create a .env file in the project root and add:

FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your_secret_key

DATABASE_URL=postgresql://postgres.vysnpajxegbyungaxxhs:JK5bADTcecJtek0N@aws-1-us-east-1.pooler.supabase.com:5432/postgres


6️⃣ Run the Application
flask run


or

python run.py

7️⃣ Access the System

Open a browser and go to:

http://127.0.0.1:5000

👥 User Roles & Credentials
Role	Default Username	Default Password
Admin	admin1	9090
Doctor	Ravi	2345
Nurse	Anne	3456
Patient	patient1	1234

⚠️ Passwords can be change after login.

👥 User Roles Supported

👨‍⚕️ Doctor

🧑‍⚕️ Nurse

🧑‍💼 Admin

🧑 Patient

Each role has controlled access to relevant dashboards and features.

🎓 Academic Purpose

This project is developed as part of an MSc in Software Engineering research initiative, focusing on:

Reducing patient waiting time

Improving fairness in hospital queues

Enhancing digital healthcare workflows in Sri Lankan hospitals

📌 Future Enhancements

Blockchain-based medical record security

Multilingual support (Sinhala / Tamil)

Advanced AI-based disease severity prediction

Mobile application integration

👩‍💻 Author

Sakna Perera
MSc Software Engineering
📍 Sri Lanka
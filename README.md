# MediFlow

MediFlow is a smart hospital queue management system designed to improve patient experience and healthcare workflow. It combines AI-driven queue prioritization with QR-based identification to streamline clinic operations and reduce wait times.

## 🚀 Features

- ✅ Implement QR Codes for Patient Identification
- 🤖 Integrate AI Queue Management for Fair and Efficient Patient Prioritization
- ⏳ Estimate Waiting Times for Patients
- 📂 Enable Instant Digital Patient Record Retrieval for Doctors
- ❓ Include a Frequently Asked Questions (FAQs) Section

## 🛠 Tech Stack

- **Frontend:** HTML, CSS, Bootstrap
- **Backend:** Python (Flask)
- **Database:** ( PostgreSQL )
- **Other:** QR Code Generation, AI Algorithm (Queue Prioritization Logic)

## 📦 Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/saknaperera/mediflow.git
   cd mediflow

# Db update tables
flask db migrate -m "Added columns to Patient table"
flask db upgrade
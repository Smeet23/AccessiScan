# 🚀 AccessiScan – Accessibility Analyzer

AccessiScan is a powerful, developer-focused web application that scans and audits websites or HTML content for accessibility compliance. It helps teams identify, understand, and resolve barriers to inclusive digital experiences—making the web a better place for everyone.

---

## 🧠 Features

- ✅ **Accessibility Analysis** using AI-powered tools
- 🌐 **Support for both URL and Raw HTML** inputs
- 📊 **Detailed Violation Report** with severity levels (Critical, Serious, Moderate, Minor)
- 🧾 **Downloadable PDF Reports** with embedded visual charts
- 📈 **Interactive Dashboard** to view history and severity breakdown
- 🔒 **Secure User Authentication** (Signup/Login/Logout)
- 📁 **Scan History Tracking** with score and timestamp
- 📉 **Severity Breakdown Charts** and Accessibility Scoring
- 👤 **User Profile Page** with scan logs and stats

---

## 🔧 Tech Stack

- **Backend**: Django (Python)
- **Frontend**: HTML, CSS, JavaScript, Chart.js
- **Database**: SQLite
- **Visualization**: Matplotlib
- **PDF Generation**: xhtml2pdf
- **Auth**: Django's built-in auth system

---

## 📥 Installation & Setup

```bash
git clone https://github.com/Smeet23/AccessiScan.git
cd accessiscan
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

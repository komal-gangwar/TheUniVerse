# The Uni Verse

An all-in-one campus platform designed to centralize and simplify student life — combining transportation, academics, communities, and AI-powered assistance into a single system.

---

## Overview

Campus systems are often fragmented across multiple platforms.  
The Uni Verse unifies essential services such as live bus tracking, academic resources, student communities, and AI-driven learning into a single, accessible interface.

---

## Features

- **Live Bus Tracking**  
  Real-time bus location using OpenStreetMap and Leaflet  

- **Academic Resources**  
  Access notes, syllabus, and previous year papers  

- **AI Virtual Teacher** *(Gemini API)*  
  - **Normal Mode:** Instant academic explanations  
  - **Practice Mode:** Auto-generated MCQs, subjective questions, and coding tasks  
  - **Counselling Mode:** Academic and personal guidance  

- **Alumni Network**  
  Connect with seniors and graduates  

- **Events & Highlights**  
  Stay updated with campus activities  

- **Faculty Directory**  
  Access faculty details and contact information  

- **Clubs & Communities**  
  Explore and join student groups  

---

## Tech Stack

**Frontend**
- HTML  
- JavaScript  
- Tailwind CSS  

**Backend**
- Flask (Python)  
- Flask-Mail  

**Database**
- Flask-SQLAlchemy  

**APIs & Integrations**
- OpenStreetMap  
- Leaflet  
- Gemini API  

---

## Architecture

- Frontend handles UI rendering and user interaction  
- Flask backend provides APIs and application logic  
- SQLAlchemy manages database operations  
- External APIs handle maps and AI-based responses  

---

## Local Setup

```bash
# Clone repository
git clone https://github.com/komal-gangwar/the-universe.git
cd the-universe

# Create virtual environment (optional)
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

---

## Environment Variables

Create a `.env` file:

```
GEMINI_API_KEY=your_api_key
MAIL_USERNAME=your_email
MAIL_PASSWORD=your_password
```

---

## Status

Under development.

---

## Author

Komal Gangwar  
https://github.com/komal-gangwar

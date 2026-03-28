# TalkBuddy — Human Connection Marketplace

Book verified people for meaningful conversations, companionship, and social connection.

## Features

- **User Registration & Auth** — Secure sign-up, login, profile management
- **Provider Profiles** — Create a provider profile with bio, rates, specialties, and availability
- **Search & Filters** — Find companions by city, language, interests, price range
- **Booking System** — Book sessions with date, time, duration, and meeting type (coffee, walk, talk, social)
- **Reviews & Ratings** — Rate providers after completed sessions
- **In-App Messaging** — Chat with providers before booking
- **Safety & Trust** — ID verification badges, report/block system, moderation
- **Admin Dashboard** — User management, report moderation, platform analytics
- **Responsive Design** — Works on desktop, tablet, and mobile

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Seed the database with demo data
python seed_data.py

# 3. Run the app
python app.py
```

Open http://localhost:5000 in your browser.

## Demo Accounts

| Role     | Email                  | Password  |
|----------|------------------------|-----------|
| Client   | user@demo.com          | demo123   |
| Provider | emma@demo.com          | demo123   |
| Admin    | admin@talkbuddy.com    | admin123  |

## Tech Stack

- **Backend:** Python / Flask
- **Database:** SQLite (via SQLAlchemy)
- **Auth:** Flask-Login
- **Frontend:** HTML5 / CSS3 / Vanilla JS
- **Fonts:** Google Fonts (Inter) + Material Icons

## Project Structure

```
talkbuddy/
├── app.py                  # Main Flask application (routes)
├── models.py               # Database models
├── config.py               # Configuration
├── seed_data.py            # Demo data seeder
├── requirements.txt        # Python dependencies
├── static/
│   ├── css/style.css       # Stylesheet
│   └── js/app.js           # Client-side JavaScript
└── templates/
    ├── base.html            # Base layout
    ├── index.html           # Landing page
    ├── auth/                # Login, Register
    ├── main/                # Dashboard, Search, Messages, Profile
    ├── provider/            # Provider pages
    ├── booking/             # Booking pages
    ├── admin/               # Admin dashboard
    └── errors/              # 404, 403
```

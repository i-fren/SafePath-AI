# SafePath AI - Women Safety Route Assistant 🛡️

AI-powered route recommendation system for women's safety with live tracking, SOS emergency, trusted contacts, and community intelligence. Built for the **AI for Civic Innovation Hackathon 2026**.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Django](https://img.shields.io/badge/Django-4.2+-green)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple)
![Leaflet](https://img.shields.io/badge/Leaflet-1.9-brightgreen)

## 🚀 Features

### 1. AI Safe Route Recommendation
- Routes scored 0-100 based on weighted safety factors
- Three route options: Shortest, Fastest, Safest (recommended)
- Interactive Leaflet.js map with crime hotspots and safe zones
- Time-aware analysis (day vs. night scoring)

### 2. Trusted Contacts System
- Add, edit, remove trusted contacts
- Store name, phone, email, relationship
- Mark primary emergency contacts
- Contacts auto-notified during emergencies

### 3. Live Location Sharing & Journey Tracking
- Start tracked journeys with real-time GPS updates
- Generate unique shareable tracking links
- Public tracking page shows: current location, route, destination, ETA, status
- Location history stored for journey replay

### 4. SOS Emergency Button
- Highly visible emergency button with pulse animation
- Captures GPS coordinates on trigger
- Alerts ALL trusted contacts with location
- Shows nearest emergency services (police, hospital)
- Quick-dial emergency numbers (15, 1122, 1043, 115)
- Resolve/cancel false alarms

### 5. Safe Arrival Confirmation
- Automatic arrival prompt at estimated time
- Configurable grace period
- If unconfirmed: marks journey, notifies contacts
- Manual "I've Arrived Safely" confirmation

### 6. Safety Check-In Timer
- Configurable intervals: 15 / 30 / 60 minutes
- Visual check-in banner during journey
- "I'm Safe" / "Need Help" options
- Missed check-in triggers emergency alert

### 7. Route Deviation Detection
- Monitors GPS vs. planned route
- 500m threshold triggers warning
- "Are you safe?" confirmation dialog
- Auto-alerts contacts if no response
- Records all deviation events

### 8. Nearby Safe Places
- Interactive map with all safe zones
- Filter by type: Police, Hospital, Pharmacy, Transit, etc.
- Distance-sorted results
- Phone numbers and operating hours
- Quick navigation links

### 9. AI Safety Assistant (Chatbot)
- Natural language safety Q&A
- Explains safety scores
- Emergency guidance
- Route safety recommendations
- Time-based travel suggestions
- Nearby safe place finder
- Reporting guidance

### 10. Smart Safety Score Engine
| Factor | Weight |
|--------|--------|
| Crime Reports | 40% |
| Community Reports | 20% |
| Street Lighting | 15% |
| Crowd Density | 15% |
| Time of Day | 10% |

Risk Levels: 🟢 Low (70-100) | 🟡 Medium (45-69) | 🔴 High (0-44)

### 11. Community Safety Intelligence
- Report: Harassment, Stalking, Poor Lighting, Suspicious Activity, Unsafe Roads
- Severity levels (1-4)
- Reports affect area safety scores in real-time
- Map visualization of all reports

### 12. Admin Dashboard
- Total/active journeys
- Active SOS alerts (highlighted in red)
- Community reports analytics
- Crime statistics by type
- Safety score trends

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 4.2+, Django REST Framework |
| Frontend | Bootstrap 5, JavaScript ES6, Leaflet.js |
| Database | SQLite (dev) / PostgreSQL (prod) |
| AI Engine | Custom Python safety algorithms |
| Maps | OpenStreetMap + Leaflet.js |
| Location | HTML5 Geolocation API |

## Quick Start

### Prerequisites
- Python 3.10+

### Installation

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run migrations
python manage.py makemigrations
python manage.py migrate

# 4. Load sample data (Lahore, Pakistan)
python manage.py load_sample_data

# 5. Start server
python manage.py runserver
```

### Access
- **App**: http://localhost:8000/
- **Admin**: http://localhost:8000/admin/ (admin/admin123)
- **API**: http://localhost:8000/api/

### Demo Accounts
- **Admin**: `admin` / `admin123`
- **User**: `demo` / `demo123`

## 📱 Pages

| Page | URL | Description |
|------|-----|-------------|
| Home | `/` | Landing page with stats |
| Route Planner | `/route-planner/` | AI route analysis with map |
| SOS Emergency | `/sos/` | Emergency button + contacts |
| Start Journey | `/journey/start/` | Begin tracked journey |
| My Journeys | `/journey/my/` | Journey history |
| Tracking Page | `/track/<uuid>/` | Public journey tracking |
| Trusted Contacts | `/contacts/` | Manage emergency contacts |
| AI Assistant | `/ai-assistant/` | Safety chatbot |
| Nearby Places | `/nearby-safe-places/` | Safe zones map |
| Community Reports | `/community-reports/` | View reports |
| Submit Report | `/submit-report/` | Report safety concern |
| Dashboard | `/dashboard/` | Analytics & monitoring |
| Safety Tips | `/safety-tips/` | Tips & emergency numbers |

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analyze-route/` | POST | AI route safety analysis |
| `/api/sos/trigger/` | POST | Trigger SOS emergency |
| `/api/sos/<id>/resolve/` | POST | Resolve SOS alert |
| `/api/journey/start/` | POST | Start tracked journey |
| `/api/journey/<uuid>/location/` | POST | Update GPS location |
| `/api/journey/<uuid>/status/` | GET | Get journey status (public) |
| `/api/journey/<uuid>/complete/` | POST | Confirm arrival |
| `/api/journey/<uuid>/checkin/` | POST | Safety check-in |
| `/api/journey/<uuid>/deviation-safe/` | POST | Confirm deviation safe |
| `/api/contacts/` | GET/POST | Trusted contacts CRUD |
| `/api/chat/` | POST | AI assistant chat |
| `/api/nearby-places/` | GET | Nearby safe places |
| `/api/safety-score/` | GET | Area safety score |
| `/api/crimes/` | GET/POST | Crime reports |
| `/api/reports/` | GET/POST | Community reports |
| `/api/safe-zones/` | GET | Safe zones list |
| `/api/dashboard-stats/` | GET | Dashboard analytics |

## Database Models

| Model | Purpose |
|-------|---------|
| CrimeReport | Crime incidents with type, severity, location |
| SafetyReport | Community safety reports (harassment, lighting, etc.) |
| SafeZone | Safe locations (police, hospitals, transit, pharmacies) |
| RouteAnalysis | Stored route analysis results |
| AreaSafetyScore | Pre-calculated grid safety scores |
| TrustedContact | Emergency contacts per user |
| Journey | Active/completed journeys with tracking |
| LocationUpdate | GPS location history for journeys |
| EmergencyAlert | SOS alerts and emergency events |
| EmergencyContactNotification | Notification delivery tracking |
| ArrivalConfirmation | Safe arrival confirmations |
| JourneyCheckIn | Periodic safety check-ins |
| RouteDeviation | Route deviation events |
| ChatMessage | AI assistant conversation history |

## Sample Data (Pakistan - Lahore)

- 28 crime reports across Lahore locations
- 20 safe zones (police stations, hospitals, metro, malls)
- 15 community safety reports
- 200 pre-calculated area safety scores

## Emergency Numbers (Pakistan)

| Service | Number |
|---------|--------|
| Police | 15 |
| Rescue 1122 | 1122 |
| Women Helpline | 1043 |
| Edhi Foundation | 115 |
| Fire Brigade | 16 |
| Motorway Police | 130 |

## Project Structure

```
safepath-ai/
├── manage.py
├── requirements.txt
├── safepath/                   # Django project
│   ├── settings.py, urls.py, wsgi.py
├── core/                      # Main application
│   ├── models.py             # 14 database models
│   ├── views.py              # Template views (all features)
│   ├── api_views.py          # REST API endpoints
│   ├── ai_engine.py          # Safety scoring algorithm
│   ├── ai_assistant.py       # AI chatbot engine
│   ├── serializers.py        # DRF serializers
│   ├── forms.py              # Django forms
│   ├── admin.py              # Admin configuration
│   ├── urls.py               # Page URLs
│   ├── api_urls.py           # API URLs
│   └── management/commands/load_sample_data.py
├── templates/
│   ├── base.html             # Base layout + navbar
│   ├── registration/         # Login/logout
│   └── core/                 # All feature templates
│       ├── home.html, route_planner.html
│       ├── sos.html, journey_detail.html
│       ├── ai_assistant.html, nearby_safe_places.html
│       ├── trusted_contacts.html, start_journey.html
│       ├── my_journeys.html, track_journey.html
│       ├── dashboard.html, community_reports.html
│       └── submit_report.html, safety_tips.html
└── static/
```

## License

Built for AI for Civic Innovation Hackathon 2026 demonstration.

# Runner Tracker Application

A Django web application for runners to track and share their running activities.

## Features

### Main Features

1. **CRUD Operations for Runs (Requirement 1)**
   - Add, edit, and delete running activities
   - Associate runs with routes
   - Track details like distance, duration, pace, weather conditions, etc.

2. **Reports and Statistics (Requirement 2)**
   - Filter runs by date range, distance, and route
   - View summary statistics (total distance, average pace, etc.)
   - Visualize running data with charts

### Additional Features

- User authentication system
- Runner profiles with personal information
- Route management
- Public/private runs visibility

## Database Schema

The application uses PostgreSQL with the following main tables:

1. **Runner** - Extended user profile information
   - Linked to Django's built-in User model
   - Stores age, height, weight, bio, etc.

2. **Route** - Information about running routes
   - Name, start/end locations, distance, elevation gain, etc.
   - Created by runners

3. **Run** - The primary table tracking running activities
   - Title, date, duration, distance, pace, etc.
   - Connected to a runner and optionally to a route

4. **Comment** - Comments on runs
   - Content, commenter, timestamp

5. **RunLike** - Tracks likes on runs
   - Many-to-many relationship between runs and runners

## Technology Stack

- **Backend**: Django 5.1
- **Database**: PostgreSQL
- **ORM**: Django ORM
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Charting**: Chart.js

## Implementation Notes

- Uses Django ORM for most database operations (80%)
- Uses raw SQL with prepared statements for complex reporting queries (20%)
- Responsive design using Bootstrap
- Interactive statistics with Chart.js

## Setup Instructions

### Prerequisites

- Python 3.10+
- PostgreSQL

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a PostgreSQL database named 'running_tracker'
5. Configure database settings in `running_tracker/settings.py`
6. Apply migrations:
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```
7. Create a superuser:
   ```
   python manage.py createsuperuser
   ```
8. Run the development server:
   ```
   python manage.py runserver
   ```
9. Access the application at http://127.0.0.1:8000/

# Customizable Learning Platform (Capstone Project)

This project is a **Capstone Project** for the completion of the Software Engineering Diploma program. It serves as an exploration of **Django** and an attempt to learn **deployment on a server**. 

The main goal of this project is to build a **customizable e-learning platform** with a focus on accessibility for students with hearing disabilities. The platform allows for **role-based access** and **course management**, where content managers can create and manage courses, and students can engage in learning activities.

### Key Features

- **User Roles**: 
  - **Normal Users** (Students)
  - **Content Managers** (Create and manage courses)
  - **Admins** (Administer the platform)
  
- **Customizable Features**:
  - Dark Mode and Color Theme adjustments
  - Font Size and Text Spacing adjustments

- **Course Management**:
  - Courses categorized by learning levels (Junior, Intermediate, Advanced)
  - Each course consists of ordered sections with various content types (Text, Images, Videos, Quizzes)
  
- **User Authentication**:
  - Email verification for new users
  - Google OAuth login (via Django Allauth)

### Technologies Used

- **Django**: The primary framework for building the web application.
- **Bootstrap 5**: For front-end styling.
- **Django Crispy Forms**: For better form rendering.
- **JavaScript**: For dynamic content (e.g., adding quizzes and formsets).
- **SQLite**: Default database used for development.
- **Nginx / Gunicorn**: For deployment on the server.

### Installation Guide

## Prerequisites
Before installation, ensure you have these installed:

1. **Python 3.8+**:
   - Download from [python.org](https://www.python.org/downloads/)
   - Check "Add Python to PATH" during installation

2. **Git**:
   - Download from [git-scm.com](https://git-scm.com/download/win)

3. **FFmpeg**:
    ```bash
    winget install ffmpeg
    ```
    
## Clone the repository 
    ```bash
    git clone https://github.com/Shadowress/Customizable-Mathematics-Learning-Website
    cd CustomizableLearningPlatform
    ```
    
## Set up a virtual environment
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

## Install dependencies
    ```bash
    pip install -r requirements.txt
    ```

## Google OAuth Setup
1. **Google Account Setup**:
   - Make sure your Google account has 2-Step Verification enabled.
   - Go to your Google App Passwords and generate an App Password. Save it.

2. **Google Cloud Console Setup**:
   - Go to Google Cloud Console.
   - Create a new project.
   - Set up OAuth 2.0 Client IDs under APIs & Services > Credentials.
   - Add the following to Authorized redirect URIs:
       - http://127.0.0.1:8000/accounts/google/login/callback/
       - http://localhost:8000/accounts/google/login/callback/
   - Save your Client ID and Client Secret.

## Environment Configurations
1. Rename .env.example to .env:
    ```bash
    ren .env.example .env
    ```

2. Open .env in Notepad:
    ```bash
    notepad .env
    ```

3. Inside .env, configure the following:
   - Generate a Django secret key:
      ```bash
      python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
      ```
   - Fill in:
      SECRET_KEY=<your-generated-secret-key>
      EMAIL_HOST_USER=<your-google-email>
      EMAIL_HOST_PASSWORD=<your-app-password>

## Database Setup
    ```bash
    python manage.py makemigrations users
    python manage.py makemigrations courses
    python manage.py migrate
    ```

    ⚠️ If you face migration issues:
       - Delete db.sqlite3
       - Delete all .py files (except __init__.py) inside each app's migrations/ folder
       - Re-run the above commands

## Collect Static Files
    ```bash
    python manage.py collectstatic
    ```

## Create Admin User
    ```bash
    python manage.py createsuperuser
    ```

## Start the Server
    ```bash
    python manage.py runserver
    ```
    Visit: http://127.0.0.1:8000

## Django Admin Configuration
    1. Go to http://127.0.0.1:8000/admin and log in with your superuser credentials.
    2. Navigate to Sites and change the domain to:
       - 127.0.0.1:8000
    3. Go to Social Applications:
       - Add a new application.
       - Choose Google as the provider.
       - Enter your Client ID and Client Secret.
       - Move 127.0.0.1:8000 from "Available sites" to "Chosen sites".
       - Save.

### Deployment

This project was also an opportunity to learn how to deploy a Django application to a live server. The deployment process involves:

1. Setting up a **production environment** using **Nginx** and **Gunicorn**.
2. Configuring **SSL certificates** for secure HTTP.
3. Using **PostgreSQL** for production data storage (as opposed to SQLite).

### License

This project is open-source, licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

> **Note**: This project was done as part of a capstone to gain practical experience with Django and deployment. It is a starting point for future improvements and enhancements.


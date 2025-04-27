# Customizable Learning Platform (Capstone Project)

This project is a **Capstone Project** for the completion of the Software Engineering Diploma program. It serves as an exploration of **Django** and an attempt to learn **deployment on a server**. 

The main goal of this project is to build a **customizable e-learning platform** with a focus on accessibility for students with hearing disabilities. The platform allows for **role-based access** and **course management**, where content managers can create and manage courses, and students can engage in learning activities.

### Key Features

- **User Roles**: 
  - **Normal Users** (Students)
  - **Content Managers** (Create and manage courses)
  - **Admins** (Administer the platform)
  
- **Customizable Features**:
  - AI Sign Language Text-to-Speech (toggle on/off)
  - Dark Mode, Font Size, and Text Spacing adjustments

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

### Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/CustomizableLearningPlatform.git
    cd CustomizableLearningPlatform
    ```

2. **Set up a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Apply migrations**:
    ```bash
    python manage.py migrate
    ```

5. **Run the development server**:
    ```bash
    python manage.py runserver
    ```

    The application will be available at `http://127.0.0.1:8000/`.

### Deployment

This project was also an opportunity to learn how to deploy a Django application to a live server. The deployment process involves:

1. Setting up a **production environment** using **Nginx** and **Gunicorn**.
2. Configuring **SSL certificates** for secure HTTP.
3. Using **PostgreSQL** for production data storage (as opposed to SQLite).
4. Automating the deployment process using **Docker** (optional) or simple bash scripts for production server setup.

### Future Work

- Add more **interactive features** for students (e.g., quizzes, assignments).
- Improve **AI sign language features** and make them more robust.
- Implement **real-time chat or support systems** for students.

### License

This project is open-source, licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

> **Note**: This project was done as part of a capstone to gain practical experience with Django and deployment. It is a starting point for future improvements and enhancements.


# AI-Powered Learning Management System (LMS)

A comprehensive, modern Learning Management System built with Flask, featuring AI-powered behavior monitoring, adaptive quizzes, and intelligent student support.

## 🚀 Features

### Core LMS Features
- **Multi-role Support**: Students, Instructors, and Admin panels
- **Course Management**: Create, manage, and enroll in courses
- **Assignment System**: Submit and grade assignments
- **Quiz System**: Adaptive quizzes with difficulty levels
- **Discussion Forums**: Interactive course discussions
- **Calendar Integration**: Track deadlines and events
- **File Management**: Upload and share course materials

### AI-Powered Features
- **Real-time Behavior Monitoring**: Track focus and frustration levels
- **Emotion Analysis**: AI-powered emotion detection using computer vision
- **Adaptive Learning**: Dynamic quiz difficulty based on performance
- **Intelligent Suggestions**: AI-generated study recommendations
- **Performance Analytics**: Detailed student progress tracking

### Advanced Features
- **Live Dashboard**: Real-time statistics and progress tracking
- **Responsive Design**: Modern, mobile-friendly interface
- **Real-time Updates**: Live data synchronization
- **Admin Panel**: Comprehensive system management
- **User Management**: Advanced user role and permission system

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **Database**: SQLAlchemy with SQLite
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **AI/ML**: DeepFace for emotion analysis
- **Real-time**: Socket.IO for live updates
- **Authentication**: Flask-Login with role-based access

## 📋 Prerequisites

- Python 3.8 or higher
- Git
- Web browser with camera access (for behavior monitoring)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <your-repository-url>
   cd ai-lms2
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```
   SECRET_KEY=your-secret-key-here
   GEMINI_API_KEY=your-gemini-api-key-here
   ```

6. **Initialize database**
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

7. **Run the application**
   ```bash
   python app.py
   ```

8. **Access the application**
   Open your browser and go to `http://localhost:5000`

## 👥 User Roles

### Student
- Enroll in courses
- Take adaptive quizzes
- Submit assignments
- View real-time behavior monitoring
- Access AI-powered study suggestions
- Track progress and performance

### Instructor
- Create and manage courses
- Design assignments and quizzes
- Grade submissions
- Monitor student behavior
- View detailed analytics
- Manage course content

### Admin
- Manage all users and courses
- System-wide analytics
- User role management
- Course oversight
- System configuration

## 🎯 Key Features in Detail

### AI Behavior Monitoring
- Real-time focus and frustration tracking
- Computer vision-based emotion analysis
- Live dashboard updates every 5 seconds
- Historical behavior data visualization

### Adaptive Quiz System
- Dynamic difficulty adjustment
- Performance-based question selection
- Real-time behavior integration
- Comprehensive result analytics

### Modern Dashboard
- Real-time statistics
- Upcoming events calendar
- AI-powered suggestions
- Motivational quotes
- Live progress tracking

## 📁 Project Structure

```
ai-lms2/
├── app.py                 # Main application file
├── config.py             # Configuration settings
├── models.py             # Database models
├── requirements.txt      # Python dependencies
├── student/              # Student blueprint
│   ├── views.py         # Student routes
│   └── behavior_monitor.py
├── instructor/           # Instructor blueprint
│   └── views.py         # Instructor routes
├── admin/               # Admin blueprint
│   └── views.py         # Admin routes
├── auth/                # Authentication blueprint
│   └── views.py         # Auth routes
├── services/            # External services
│   └── gemini_service.py
├── templates/           # HTML templates
│   ├── base.html
│   ├── student_dashboard.html
│   ├── instructor_dashboard.html
│   └── admin/
├── static/              # Static files (CSS, JS, images)
└── uploads/             # File uploads directory
```

## 🔧 Configuration

### Environment Variables
- `SECRET_KEY`: Flask secret key for session management
- `GEMINI_API_KEY`: Google Gemini API key for AI features
- `DATABASE_URL`: Database connection string (optional)

### Database Configuration
The application uses SQLite by default. For production, consider using PostgreSQL or MySQL.

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production Deployment
1. Set up a production web server (Gunicorn, uWSGI)
2. Configure environment variables
3. Set up a production database
4. Configure SSL certificates
5. Set up monitoring and logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Flask framework and community
- Bootstrap for responsive design
- DeepFace for emotion analysis
- Google Gemini for AI features

## 📞 Support

For support and questions, please open an issue in the GitHub repository or contact the development team.

---

**Built with ❤️ for modern education** 
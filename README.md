# CS Journal 4.0

A modern Django-based academic journal management system for publishing and managing scholarly articles, built with internationalization support and rich content editing capabilities.

## 🌟 Features

- **Multi-language Support**: Built-in internationalization with Django's i18n framework and django-rosetta for translation management
- **Rich Text Editing**: CKEditor integration for advanced content creation and editing
- **Article Management**: Comprehensive system for managing journal articles, issues, and volumes
- **Subscription System**: Built-in subscription management for journal access
- **Submission Guidelines**: Configurable submission and permission systems
- **Mailing List**: Subscriber management with automated content alerts
- **Admin Interface**: Full Django admin integration for content management
- **Responsive Design**: Modern, mobile-friendly interface using TailwindCSS and Flowbite
- **SEO Optimized**: Meta tags and sitemap generation for better search engine visibility

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/My-name-is-Jamshidbek/cs_jounral4.0.git
   cd cs_jounral4.0
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Database setup**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Seed the database with sample data**
   ```bash
   python manage.py setup_journal
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Frontend: http://127.0.0.1:8000/
   - Admin Panel: http://127.0.0.1:8000/admin/

## 📋 Management Commands

This project includes several custom Django management commands for easy setup and data management:

### Complete Setup
```bash
# Complete database setup with default data
python manage.py setup_journal

# With custom counts
python manage.py setup_journal --articles 50 --subscribers 100
```

### Individual Commands
```bash
# Seed core data (clears existing data)
python manage.py seed_db --clear

# Add sample articles
python manage.py seed_articles --count 25

# Add sample subscribers
python manage.py seed_subscribers --count 50
```

## 🏗️ Project Structure

```
cs_jounral4.0/
├── about/              # About pages and content
├── config/             # Django settings and configuration
├── core/               # Main application logic
│   ├── management/     # Custom management commands
│   ├── models.py       # Core data models
│   └── views.py        # Core views
├── issue/              # Journal issues and articles management
├── locale/             # Internationalization files
├── submit/             # Submission guidelines and permissions
├── subscribe/          # Subscription system
├── templates/          # HTML templates
├── manage.py           # Django management script
└── requirements.txt    # Python dependencies
```

## 🌐 Internationalization

The project supports multiple languages through Django's internationalization framework:

- **Translation Management**: Use django-rosetta at `/rosetta/` to manage translations
- **Language Files**: Located in `locale/` directory
- **Supported Languages**: English (default) with extensible support for additional languages

### Managing Translations

1. **Extract translatable strings**
   ```bash
   python manage.py makemessages -l en
   python manage.py makemessages -l [your_language_code]
   ```

2. **Compile translations**
   ```bash
   python manage.py compilemessages
   ```

3. **Use Rosetta interface**
   - Access `/rosetta/` in your browser (admin login required)
   - Edit translations directly through the web interface

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root for local development:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
```

### Settings

Key configuration options in `config/settings.py`:

- **ALLOWED_HOSTS**: Configure allowed hosts for production
- **CSRF_TRUSTED_ORIGINS**: Set trusted origins for CSRF protection
- **MEDIA_ROOT**: File upload directory
- **STATIC_ROOT**: Static files directory for production
- **CKEditor**: Rich text editor configuration

### Production Deployment

For production deployment:

1. Set `DEBUG = False`
2. Configure proper `SECRET_KEY`
3. Set up `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`
4. Configure static file serving
5. Set up proper database (PostgreSQL recommended)
6. Configure email backend for notifications

## 📚 Key Models

### Core Models

- **Joining**: Mailing list subscriber requests
- **Default**: Site-wide configuration settings

### Issue Models

- **Issue**: Journal volumes and issues
- **JournalIssue**: Individual articles within issues

### About Models

- **About**: Static content pages (About Us, Editorial Board, etc.)

### Submit Models

- **Permission**: Submission guidelines and access policies

### Subscribe Models

- **Subscribe**: Subscription-related content and policies

## 🎨 Frontend

The frontend uses:

- **TailwindCSS**: For utility-first CSS styling
- **Flowbite**: For interactive components
- **Alpine.js**: For lightweight JavaScript interactions
- **Responsive Design**: Mobile-first approach

## 🛠️ Development

### Running Tests

```bash
python manage.py test
```

### Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to classes and functions
- Keep functions small and focused

### Adding New Features

1. Create new Django apps for major features
2. Add models in the appropriate app
3. Create migrations: `python manage.py makemigrations`
4. Apply migrations: `python manage.py migrate`
5. Add admin configuration if needed
6. Create views and templates
7. Add URL patterns
8. Add translations for new strings

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Commit your changes: `git commit -am 'Add new feature'`
7. Push to the branch: `git push origin feature/new-feature`
8. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Links

- **Live Site**: [jurnal-komparativistika.uz](https://jurnal-komparativistika.uz)
- **Admin Panel**: [jurnal-komparativistika.uz/admin](https://jurnal-komparativistika.uz/admin)

## 📞 Support

For support and questions:

- Create an issue in this repository
- Contact the development team
- Check the documentation in the code comments

## 🚀 Recent Updates

- Django 4.2.23 for enhanced security and performance
- Integrated CKEditor for rich content creation
- Multi-language support with django-rosetta
- Comprehensive management commands for easy setup
- Modern responsive design with TailwindCSS

---

**Built with ❤️ for the academic community**
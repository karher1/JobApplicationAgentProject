# Job Application Automation

An AI-powered job search and application automation system that helps users find, match, and apply to jobs efficiently.

## 🚀 Features

### ✅ **Completed Modules**
- **Module 1: User Profile DB** - Complete user profile management with skills, experience, and preferences
- **Module 3: Enhanced Job Description Extractor** - AI-powered job description parsing and extraction
- **Module 8: Daily Digest Generator** - Personalized daily email summaries with job matches and insights

### 🔧 **Core Features**
- **Smart Job Matching** - AI-powered job matching using vector similarity
- **Automated Form Filling** - Selenium-based form extraction and filling
- **Email Notifications** - Daily digest emails with personalized content
- **Profile Management** - Comprehensive user profile with skills and experience tracking
- **Application Tracking** - Track job applications and their status

## 📁 Project Structure

```
JobApplicationAgent/
├── 📁 src/                          # Main source code
│   ├── 📁 api/                      # FastAPI application
│   │   ├── main.py                  # Main FastAPI app
│   │   └── routes/                  # API route modules
│   ├── 📁 core/                     # Core application logic
│   │   └── config.py                # Configuration management
│   ├── 📁 models/                   # Pydantic models
│   ├── 📁 services/                 # Business logic services
│   └── 📁 utils/                    # Utility functions
├── 📁 database/                     # Database schemas and migrations
│   ├── 📁 schemas/                  # Schema definitions
│   └── supabase_digest_tables.sql   # Ready-to-paste for Supabase
├── 📁 tests/                        # All test files
│   ├── 📁 unit/                     # Unit tests
│   ├── 📁 integration/              # Integration tests
│   └── 📁 e2e/                      # End-to-end tests
├── 📁 scripts/                      # Utility scripts
├── 📁 data/                         # Data files
├── 📁 docs/                         # Documentation
├── 📁 legacy/                       # Old/legacy files
├── 📁 config/                       # Configuration files
├── requirements.txt                 # Main requirements
├── requirements-dev.txt             # Development requirements
└── run.py                          # Application entry point
```

## 🛠️ Setup

### 1. **Clone and Install**
```bash
git clone <repository-url>
cd JobApplicationAgent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. **Environment Configuration**
Create a `.env` file in the root directory:
```env
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=job-embeddings

# Email Configuration (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=noreply@jobapplicationagent.com
FROM_NAME=Job Application Agent

# Application Configuration
BASE_URL=http://localhost:8000
DEBUG=true
```

### 3. **Database Setup**
1. Set up a Supabase project
2. Run the SQL from `database/supabase_digest_tables.sql` in your Supabase SQL editor
3. Update your `.env` with Supabase credentials

### 4. **Run the Application**
```bash
python run.py
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

#### User Management
- `POST /api/users` - Create user
- `GET /api/users/{user_id}/profile` - Get user profile
- `PUT /api/users/{user_id}` - Update user

#### Job Search & Matching
- `POST /api/jobs/search` - Search for jobs
- `GET /api/jobs` - Get stored jobs
- `POST /api/users/{user_id}/match-jobs` - Find matching jobs

#### Job Applications
- `POST /api/jobs/{job_id}/apply` - Apply to a job
- `GET /api/jobs/{job_id}` - Get job details

#### Digest System
- `POST /api/v1/digest/generate` - Generate daily digest
- `GET /api/v1/digest/schedules` - Get digest schedules
- `GET /api/v1/digest/stats` - Get digest statistics

## 🧪 Testing

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test Categories
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# End-to-end tests
pytest tests/e2e/
```

### Run Individual Test Files
```bash
# Test user profile functionality
pytest tests/unit/test_user_profile.py

# Test digest generation
pytest tests/unit/test_digest.py

# Test job extraction
pytest tests/unit/test_job_extraction.py
```

## 🔧 Development

### Install Development Dependencies
```bash
pip install -r requirements-dev.txt
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## 📖 Documentation

- **Project Architecture**: `docs/PROJECT_ARCHITECTURE.md`
- **API Documentation**: Available at `/docs` when server is running
- **Setup Guide**: This README
- **Legacy Code**: See `legacy/` directory for old implementations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the documentation in `docs/`
2. Review existing issues
3. Create a new issue with detailed information

## 🚀 Deployment

### Local Development
```bash
python run.py
```

### Production
```bash
# Set DEBUG=false in .env
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### Docker (Coming Soon)
```bash
docker build -t job-application-agent .
docker run -p 8000:8000 job-application-agent
```

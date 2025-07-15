# Job Application Automation System

A comprehensive AI-powered platform that automates the entire job search and application process. This full-stack application includes a web interface, REST API, Chrome browser extension, and intelligent automation features to streamline job hunting.

## 🚀 Features

### ✅ **Core Components**
- **🌐 Web Application** - Next.js frontend with modern UI components
- **⚡ REST API** - FastAPI backend with comprehensive endpoints
- **🔌 Browser Extension** - Chrome extension for automated form filling
- **🤖 AI Integration** - OpenAI/Anthropic LLM integration for content generation
- **📊 Analytics Dashboard** - Job search statistics and application tracking

### 🎯 **Key Capabilities**
- **Smart Job Search** - Multi-platform job scraping from 50+ companies (Stripe, Figma, Linear, etc.)
- **Intelligent Matching** - Vector-based job matching using user profiles and preferences
- **Resume Parsing** - Automatic extraction of skills, experience, and education from resumes
- **Auto-Application** - Automated form filling and job application submission
- **Content Generation** - AI-powered cover letters and application responses
- **Real-time Chat** - Interactive chatbot for career guidance and job search assistance
- **Notification System** - Daily digest emails with personalized job recommendations

## 📁 Project Structure

```
JobApplicationAgent/
├── 📁 frontend/                     # Next.js Web Application
│   ├── 📁 src/app/                  # App Router pages and layouts
│   ├── 📁 src/components/           # React components
│   ├── 📁 src/lib/                  # API clients and utilities
│   ├── package.json                # Frontend dependencies
│   └── next.config.ts               # Next.js configuration
├── 📁 src/                          # Backend API (FastAPI)
│   ├── 📁 api/                      # API routes and middleware
│   │   ├── main.py                  # Main FastAPI app
│   │   └── routes/                  # Feature-specific routes
│   ├── 📁 services/                 # Business logic services
│   │   ├── job_search_service.py    # Job scraping and search
│   │   ├── user_profile_service.py  # User management
│   │   ├── resume_parsing_service.py # Resume parsing and extraction
│   │   └── job_scrapers/            # Company-specific scrapers
│   ├── 📁 models/                   # Pydantic data models
│   ├── 📁 core/                     # Configuration and settings
│   └── 📁 utils/                    # Utility functions
├── 📁 browser-extension/            # Chrome Extension
│   ├── manifest.json               # Extension manifest
│   ├── popup.html                  # Extension popup interface
│   ├── background.js               # Service worker
│   └── content-script.js           # Page interaction scripts
├── 📁 database/                     # Database management
│   ├── 📁 schemas/                  # SQL schema definitions
│   └── 📁 migrations/               # Database migrations
├── 📁 data/                         # Application data
│   ├── 📁 cache/                    # Job search result cache
│   └── 📁 templates/                # Email and content templates
├── 📁 scripts/                      # Setup and utility scripts
├── 📁 tests/                        # Test suites
├── 📁 docs/                         # Documentation
├── .env.example                     # Environment template
├── requirements.txt                 # Python dependencies
└── run.py                          # Application launcher
```

## 🛠️ Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Supabase account (free tier available)
- OpenAI or Anthropic API key

### 1. **Backend Setup**
```bash
# Clone and setup Python environment
git clone <repository-url>
cd JobApplicationAgent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. **Frontend Setup**
```bash
# Setup Next.js frontend
cd frontend
npm install
```

### 3. **Environment Configuration**
Copy `.env.example` to `.env` and configure:
```env
# Required: Database
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key

# Required: AI Services (choose one or both)
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Optional: Vector Database for advanced matching
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=us-west1-gcp-free
PINECONE_INDEX_NAME=job-embeddings
```

### 4. **Database Setup**
```bash
# Run database migrations
python scripts/setup_supabase.py
```

### 5. **Start the Application**
```bash
# Terminal 1: Start backend (port 8000)
source venv/bin/activate
python run.py

# Terminal 2: Start frontend (port 3000)
cd frontend
npm run dev
```

**Access the application:**
- 🌐 **Web App**: http://localhost:3000
- 📚 **API Docs**: http://localhost:8000/docs
- 🔧 **API Health**: http://localhost:8000/health

## 📱 Application Features

### 🎯 **Job Search & Discovery**
- **Multi-Platform Scraping**: 50+ companies including Stripe, Figma, Linear, Notion, HashiCorp
- **Smart Filters**: Location, salary, job type, remote options
- **Cached Results**: 6-hour cache for faster subsequent searches
- **Real-time Updates**: Fresh job postings updated regularly

### 👤 **User Profile Management**
- **Resume Upload & Parsing**: Automatic extraction of skills, experience, education
- **Skills Management**: Categorized skills with proficiency levels
- **Experience Tracking**: Work history with detailed job descriptions
- **Preference Settings**: Job titles, locations, salary ranges

### 🤖 **AI-Powered Features**
- **Content Generation**: Cover letters, application responses
- **Job Matching**: Vector similarity matching based on profile
- **Resume Analysis**: Skill extraction and profile optimization
- **Career Chat**: Interactive guidance and job search assistance

### 📊 **Analytics & Tracking**
- **Application History**: Track all job applications and their status
- **Search Analytics**: Monitor search patterns and success rates
- **Performance Metrics**: Application response rates and insights

## 📚 API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Core API Endpoints

#### 🔍 Job Search
```http
POST /api/jobs/search
GET /api/jobs?limit=50&offset=0
GET /api/v2/jobs/companies
POST /api/v2/jobs/search/companies
```

#### 👤 User Management
```http
GET /api/users/{user_id}/profile
PUT /api/users/{user_id}/preferences
POST /api/users/{user_id}/resumes
POST /api/users/{user_id}/resumes/{resume_id}/parse
```

#### 🎯 Job Applications
```http
POST /api/jobs/{job_id}/apply
POST /api/jobs/batch-apply
GET /api/users/{user_id}/applications
```

#### 🤖 AI Services
```http
POST /api/chatbot/start
POST /api/chatbot/{conversation_id}/message
POST /api/resume/review
POST /api/ai/generate-content
```

## 🔌 Browser Extension

### Installation
1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked" and select the `browser-extension/` directory
4. The extension icon will appear in your browser toolbar

### Features
- **Auto-fill Applications**: Automatically populate job application forms
- **Form Detection**: Intelligent form field recognition and mapping
- **Profile Integration**: Sync with your user profile for consistent information
- **Application Tracking**: Track applications submitted through the extension

## 🧪 Testing & Development

### Backend Testing
```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/e2e/          # End-to-end tests

# Test specific functionality
pytest tests/unit/test_user_profile.py
pytest tests/unit/test_job_extraction.py
```

### Frontend Testing
```bash
cd frontend

# Run Jest tests
npm test

# Run E2E tests with Playwright (if configured)
npm run test:e2e

# Build for production
npm run build
```

### Code Quality
```bash
# Backend code formatting
black src/ tests/
flake8 src/ tests/
mypy src/

# Frontend code formatting
cd frontend
npm run lint
npm run type-check
```

## 🏗️ Architecture

### Tech Stack
- **Backend**: FastAPI, Python 3.9+, Pydantic
- **Frontend**: Next.js 15, React 19, TypeScript, TailwindCSS
- **Database**: Supabase (PostgreSQL)
- **AI/ML**: OpenAI GPT-4, Anthropic Claude, Pinecone Vector DB
- **Caching**: File-based caching with TTL
- **Extension**: Chrome Extension Manifest V3

### Service Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Browser       │    │   Backend API   │
│   (Next.js)     │◄──►│   Extension     │◄──►│   (FastAPI)     │
│   Port 3000     │    │   (Chrome)      │    │   Port 8000     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                                              │
         │              ┌─────────────────┐             │
         └─────────────►│   Supabase      │◄────────────┘
                        │   (PostgreSQL)  │
                        └─────────────────┘
                                │
                        ┌─────────────────┐
                        │   External APIs │
                        │   OpenAI/Claude │
                        │   Pinecone      │
                        │   Job Boards    │
                        └─────────────────┘
```

## 🚀 Deployment

### Local Development
```bash
# Backend
source venv/bin/activate
python run.py

# Frontend
cd frontend && npm run dev
```

### Production Deployment
```bash
# Backend (production mode)
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4

# Frontend (build and serve)
cd frontend
npm run build
npm start
```

### Environment Variables for Production
```env
APP_ENV=production
DEBUG=false
CORS_ORIGINS=https://yourdomain.com
LOG_LEVEL=WARNING
```

## 📖 Documentation

### Available Documentation
- **📋 Project Architecture**: `docs/PROJECT_ARCHITECTURE.md`
- **🧪 Testing Plan**: `TESTING_PLAN.md`
- **📝 API Docs**: http://localhost:8000/docs (when running)
- **🔧 Extension Setup**: `browser-extension/README.md`

### Additional Resources
- **Database Schema**: `database/schemas/`
- **Migration Scripts**: `database/migrations/`
- **Example Configurations**: `.env.example`
- **Legacy Implementations**: `legacy/` directory

## 🤝 Contributing

### Development Workflow
1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Make** your changes with proper tests
4. **Test** thoroughly: `pytest tests/` and `npm test`
5. **Commit** with clear messages: `git commit -m 'Add amazing feature'`
6. **Push** to your branch: `git push origin feature/amazing-feature`
7. **Submit** a pull request

### Code Standards
- **Python**: Follow PEP 8, use type hints, add docstrings
- **TypeScript**: Use strict mode, proper typing, ESLint compliance
- **Testing**: Maintain >80% code coverage
- **Documentation**: Update README and docs for new features

## 🆘 Support & Troubleshooting

### Common Issues
1. **Database Connection**: Verify Supabase credentials in `.env`
2. **AI API Limits**: Check API key validity and usage limits
3. **Port Conflicts**: Ensure ports 3000 and 8000 are available
4. **Extension Issues**: Reload extension after code changes

### Getting Help
1. **Check Documentation**: Review `docs/` directory
2. **Search Issues**: Look through existing GitHub issues
3. **Create Issue**: Provide detailed reproduction steps
4. **Community**: Join discussions in the repository

### Health Checks
- **Backend Health**: http://localhost:8000/health
- **Database Status**: Check Supabase dashboard
- **API Documentation**: http://localhost:8000/docs

---

## 📊 Project Status

**Current Version**: 1.0.0 (In Development)
**Last Updated**: 2025-01-15
**Status**: ✅ Core features functional, 🔧 UI improvements ongoing

**Key Achievements**:
- ✅ Multi-platform job scraping (50+ companies)
- ✅ Resume parsing and profile management
- ✅ AI-powered content generation
- ✅ Browser extension for form automation
- ✅ Real-time chat interface
- ✅ Comprehensive API with 30+ endpoints

**Roadmap**:
- 🔄 Enhanced UI/UX improvements
- 🔄 Advanced analytics dashboard
- 📋 Mobile application
- 📋 Enterprise features and scaling

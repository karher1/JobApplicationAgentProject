-- User Profile Database Schema
-- This schema supports multiple resumes, skills tracking, and user preferences

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    linkedin_url VARCHAR(500),
    github_url VARCHAR(500),
    portfolio_url VARCHAR(500),
    location VARCHAR(255),
    timezone VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add missing columns to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS linkedin_url TEXT,
ADD COLUMN IF NOT EXISTS location TEXT,
ADD COLUMN IF NOT EXISTS portfolio_url TEXT,
ADD COLUMN IF NOT EXISTS phone TEXT;

-- User preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    preferred_job_titles TEXT[] DEFAULT '{}',
    preferred_locations TEXT[] DEFAULT '{}',
    preferred_companies TEXT[] DEFAULT '{}',
    salary_min INTEGER,
    salary_max INTEGER,
    remote_preference VARCHAR(20) DEFAULT 'any', -- 'remote', 'hybrid', 'onsite', 'any'
    job_type_preference VARCHAR(20) DEFAULT 'any', -- 'fulltime', 'parttime', 'contract', 'any'
    experience_level VARCHAR(20) DEFAULT 'any', -- 'entry', 'mid', 'senior', 'lead', 'any'
    industry_preferences TEXT[] DEFAULT '{}',
    technology_preferences TEXT[] DEFAULT '{}',
    application_limit_per_day INTEGER DEFAULT 10,
    auto_apply_enabled BOOLEAN DEFAULT FALSE,
    email_notifications_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Resumes table (supports multiple resumes per user)
CREATE TABLE IF NOT EXISTS resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL, -- e.g., "Software Engineer Resume", "Data Scientist Resume"
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(10) NOT NULL, -- 'pdf', 'docx', 'txt'
    file_size INTEGER NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Resume content table (for text extraction and analysis)
CREATE TABLE IF NOT EXISTS resume_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID REFERENCES resumes(id) ON DELETE CASCADE,
    extracted_text TEXT,
    parsed_json JSONB, -- Structured data from resume parsing
    embedding_vector VECTOR(1536), -- Pinecone embedding
    last_parsed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(resume_id)
);

-- Skills table
CREATE TABLE IF NOT EXISTS skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(100), -- 'programming', 'framework', 'tool', 'language', 'soft_skill'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User skills table (many-to-many relationship)
CREATE TABLE IF NOT EXISTS user_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    skill_id UUID REFERENCES skills(id) ON DELETE CASCADE,
    proficiency_level VARCHAR(20) DEFAULT 'intermediate', -- 'beginner', 'intermediate', 'advanced', 'expert'
    years_of_experience INTEGER,
    is_highlighted BOOLEAN DEFAULT FALSE, -- For featured skills
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, skill_id)
);

-- Work experience table
CREATE TABLE IF NOT EXISTS work_experience (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    company_name VARCHAR(255) NOT NULL,
    job_title VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    start_date DATE NOT NULL,
    end_date DATE, -- NULL for current position
    is_current BOOLEAN DEFAULT FALSE,
    description TEXT,
    achievements TEXT[],
    technologies_used TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Education table
CREATE TABLE IF NOT EXISTS education (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    institution_name VARCHAR(255) NOT NULL,
    degree VARCHAR(255) NOT NULL,
    field_of_study VARCHAR(255),
    location VARCHAR(255),
    start_date DATE,
    end_date DATE,
    is_current BOOLEAN DEFAULT FALSE,
    gpa DECIMAL(3,2),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Certifications table
CREATE TABLE IF NOT EXISTS certifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    issuing_organization VARCHAR(255) NOT NULL,
    issue_date DATE,
    expiry_date DATE,
    credential_id VARCHAR(255),
    credential_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Application history table (for tracking applications)
CREATE TABLE IF NOT EXISTS application_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    job_id VARCHAR(255), -- Reference to jobs table
    resume_id UUID REFERENCES resumes(id),
    application_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'applied', -- 'applied', 'interviewing', 'offered', 'rejected', 'withdrawn'
    notes TEXT,
    follow_up_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id);
CREATE INDEX IF NOT EXISTS idx_resumes_primary ON resumes(user_id, is_primary) WHERE is_primary = TRUE;
CREATE INDEX IF NOT EXISTS idx_user_skills_user_id ON user_skills(user_id);
CREATE INDEX IF NOT EXISTS idx_user_skills_skill_id ON user_skills(skill_id);
CREATE INDEX IF NOT EXISTS idx_work_experience_user_id ON work_experience(user_id);
CREATE INDEX IF NOT EXISTS idx_education_user_id ON education(user_id);
CREATE INDEX IF NOT EXISTS idx_certifications_user_id ON certifications(user_id);
CREATE INDEX IF NOT EXISTS idx_application_history_user_id ON application_history(user_id);
CREATE INDEX IF NOT EXISTS idx_application_history_job_id ON application_history(job_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_resumes_updated_at BEFORE UPDATE ON resumes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_work_experience_updated_at BEFORE UPDATE ON work_experience FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_education_updated_at BEFORE UPDATE ON education FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_certifications_updated_at BEFORE UPDATE ON certifications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_application_history_updated_at BEFORE UPDATE ON application_history FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert some common skills
INSERT INTO skills (name, category) VALUES
-- Programming Languages
('Python', 'programming'),
('JavaScript', 'programming'),
('TypeScript', 'programming'),
('Java', 'programming'),
('C++', 'programming'),
('C#', 'programming'),
('Go', 'programming'),
('Rust', 'programming'),
('PHP', 'programming'),
('Ruby', 'programming'),
('Swift', 'programming'),
('Kotlin', 'programming'),

-- Frameworks
('React', 'framework'),
('Vue.js', 'framework'),
('Angular', 'framework'),
('Node.js', 'framework'),
('Django', 'framework'),
('Flask', 'framework'),
('FastAPI', 'framework'),
('Spring Boot', 'framework'),
('Express.js', 'framework'),
('Laravel', 'framework'),
('Ruby on Rails', 'framework'),

-- Tools & Technologies
('Docker', 'tool'),
('Kubernetes', 'tool'),
('AWS', 'tool'),
('Azure', 'tool'),
('Google Cloud', 'tool'),
('Git', 'tool'),
('Jenkins', 'tool'),
('GitHub Actions', 'tool'),
('MongoDB', 'tool'),
('PostgreSQL', 'tool'),
('MySQL', 'tool'),
('Redis', 'tool'),
('Elasticsearch', 'tool'),
('Kafka', 'tool'),
('RabbitMQ', 'tool'),

-- Soft Skills
('Leadership', 'soft_skill'),
('Communication', 'soft_skill'),
('Problem Solving', 'soft_skill'),
('Team Collaboration', 'soft_skill'),
('Project Management', 'soft_skill'),
('Agile', 'soft_skill'),
('Scrum', 'soft_skill'),
('Customer Service', 'soft_skill'),
('Analytical Thinking', 'soft_skill'),
('Creativity', 'soft_skill')
ON CONFLICT (name) DO NOTHING; 
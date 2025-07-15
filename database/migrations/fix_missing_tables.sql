-- Database Migration: Fix Missing Tables and Columns
-- This migration adds all the missing tables and columns that the application expects

-- 1. Add missing columns to existing tables
ALTER TABLE job_applications 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- 2. Create user_preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    preferred_job_titles JSONB DEFAULT '[]',
    preferred_locations JSONB DEFAULT '[]',
    preferred_salary_min INTEGER,
    preferred_salary_max INTEGER,
    preferred_job_types JSONB DEFAULT '[]',
    remote_preference BOOLEAN DEFAULT FALSE,
    notification_frequency VARCHAR(50) DEFAULT 'daily',
    preferred_time TIME DEFAULT '09:00:00',
    timezone VARCHAR(100) DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- 3. Create skills table
CREATE TABLE IF NOT EXISTS skills (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(100),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Create user_skills table
CREATE TABLE IF NOT EXISTS user_skills (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    proficiency_level VARCHAR(50) DEFAULT 'Intermediate',
    years_of_experience INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, skill_id)
);

-- 5. Create work_experience table
CREATE TABLE IF NOT EXISTS work_experience (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_name VARCHAR(200) NOT NULL,
    job_title VARCHAR(200) NOT NULL,
    location VARCHAR(200),
    start_date DATE NOT NULL,
    end_date DATE,
    is_current BOOLEAN DEFAULT FALSE,
    description TEXT,
    achievements JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. Create education table
CREATE TABLE IF NOT EXISTS education (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    institution_name VARCHAR(200) NOT NULL,
    degree VARCHAR(200) NOT NULL,
    field_of_study VARCHAR(200),
    location VARCHAR(200),
    start_date DATE,
    end_date DATE,
    is_current BOOLEAN DEFAULT FALSE,
    gpa DECIMAL(3,2),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. Create certifications table
CREATE TABLE IF NOT EXISTS certifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    issuing_organization VARCHAR(200),
    issue_date DATE,
    expiry_date DATE,
    credential_id VARCHAR(100),
    credential_url VARCHAR(500),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8. Create resumes table
CREATE TABLE IF NOT EXISTS resumes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    file_path VARCHAR(500),
    file_name VARCHAR(200),
    file_size INTEGER,
    is_primary BOOLEAN DEFAULT FALSE,
    version VARCHAR(50) DEFAULT '1.0',
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 9. Create application_history table
CREATE TABLE IF NOT EXISTS application_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_title VARCHAR(200) NOT NULL,
    company VARCHAR(200) NOT NULL,
    application_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'applied',
    notes TEXT,
    follow_up_date DATE,
    interview_date DATE,
    offer_received BOOLEAN DEFAULT FALSE,
    offer_amount INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 10. Create jobs table (for storing job data)
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    company VARCHAR(200) NOT NULL,
    location VARCHAR(200),
    url VARCHAR(500) UNIQUE NOT NULL,
    job_board VARCHAR(100) DEFAULT 'Unknown',
    description_snippet TEXT,
    full_description TEXT,
    salary_range VARCHAR(200),
    job_type VARCHAR(100),
    remote_type VARCHAR(100),
    experience_level VARCHAR(100),
    skills_required JSONB DEFAULT '[]',
    benefits JSONB DEFAULT '[]',
    posted_date DATE,
    application_deadline DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 11. Create job_descriptions table
CREATE TABLE IF NOT EXISTS job_descriptions (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    requirements TEXT,
    responsibilities TEXT,
    benefits TEXT,
    skills JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 12. Create digest_preferences table
CREATE TABLE IF NOT EXISTS digest_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    include_job_matches BOOLEAN DEFAULT TRUE,
    include_applications BOOLEAN DEFAULT TRUE,
    include_insights BOOLEAN DEFAULT TRUE,
    include_stats BOOLEAN DEFAULT TRUE,
    max_job_matches INTEGER DEFAULT 10,
    max_application_updates INTEGER DEFAULT 20,
    preferred_job_types JSONB DEFAULT '[]',
    preferred_locations JSONB DEFAULT '[]',
    salary_range_min INTEGER,
    salary_range_max INTEGER,
    notification_frequency VARCHAR(50) DEFAULT 'daily',
    preferred_time TIME DEFAULT '09:00:00',
    timezone VARCHAR(100) DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- 13. Create generated_digests table
CREATE TABLE IF NOT EXISTS generated_digests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    digest_type VARCHAR(50) NOT NULL,
    digest_date DATE NOT NULL,
    content JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    UNIQUE(user_id, digest_date, digest_type)
);

-- 14. Create notification_configs table
CREATE TABLE IF NOT EXISTS notification_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    email_address VARCHAR(255),
    slack_webhook TEXT,
    webhook_url TEXT,
    phone_number VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, notification_type)
);

-- 15. Create notification_history table
CREATE TABLE IF NOT EXISTS notification_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    digest_id INTEGER REFERENCES generated_digests(id) ON DELETE SET NULL,
    subject VARCHAR(500) NOT NULL,
    content_preview TEXT,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'sent',
    error_message TEXT,
    delivery_time FLOAT,
    metadata JSONB DEFAULT '{}'
);

-- 16. Create email_templates table
CREATE TABLE IF NOT EXISTS email_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    subject_template TEXT NOT NULL,
    html_template TEXT NOT NULL,
    text_template TEXT NOT NULL,
    variables JSONB DEFAULT '[]',
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 17. Create digest_schedules table
CREATE TABLE IF NOT EXISTS digest_schedules (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    digest_type VARCHAR(50) NOT NULL,
    frequency VARCHAR(50) NOT NULL DEFAULT 'daily',
    preferred_time TIME DEFAULT '09:00:00',
    timezone VARCHAR(100) DEFAULT 'UTC',
    is_active BOOLEAN DEFAULT TRUE,
    last_sent TIMESTAMP WITH TIME ZONE,
    next_scheduled TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, digest_type)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_skills_user_id ON user_skills(user_id);
CREATE INDEX IF NOT EXISTS idx_user_skills_skill_id ON user_skills(skill_id);
CREATE INDEX IF NOT EXISTS idx_work_experience_user_id ON work_experience(user_id);
CREATE INDEX IF NOT EXISTS idx_education_user_id ON education(user_id);
CREATE INDEX IF NOT EXISTS idx_certifications_user_id ON certifications(user_id);
CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id);
CREATE INDEX IF NOT EXISTS idx_application_history_user_id ON application_history(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_url ON jobs(url);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_job_descriptions_job_id ON job_descriptions(job_id);
CREATE INDEX IF NOT EXISTS idx_digest_preferences_user_id ON digest_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_generated_digests_user_date ON generated_digests(user_id, digest_date);
CREATE INDEX IF NOT EXISTS idx_notification_configs_user_id ON notification_configs(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_history_user_id ON notification_history(user_id);
CREATE INDEX IF NOT EXISTS idx_digest_schedules_user_id ON digest_schedules(user_id);

-- Create triggers for updated_at
CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_skills_updated_at BEFORE UPDATE ON user_skills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_work_experience_updated_at BEFORE UPDATE ON work_experience
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_education_updated_at BEFORE UPDATE ON education
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_certifications_updated_at BEFORE UPDATE ON certifications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_resumes_updated_at BEFORE UPDATE ON resumes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_application_history_updated_at BEFORE UPDATE ON application_history
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_job_descriptions_updated_at BEFORE UPDATE ON job_descriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_digest_preferences_updated_at BEFORE UPDATE ON digest_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_configs_updated_at BEFORE UPDATE ON notification_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_email_templates_updated_at BEFORE UPDATE ON email_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_digest_schedules_updated_at BEFORE UPDATE ON digest_schedules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default skills
INSERT INTO skills (name, category, description) VALUES
('Python', 'Programming', 'Python programming language'),
('JavaScript', 'Programming', 'JavaScript programming language'),
('Java', 'Programming', 'Java programming language'),
('React', 'Frontend', 'React.js framework'),
('Node.js', 'Backend', 'Node.js runtime environment'),
('SQL', 'Database', 'Structured Query Language'),
('MongoDB', 'Database', 'NoSQL database'),
('AWS', 'Cloud', 'Amazon Web Services'),
('Docker', 'DevOps', 'Containerization platform'),
('Kubernetes', 'DevOps', 'Container orchestration'),
('Selenium', 'Testing', 'Web automation testing'),
('Cypress', 'Testing', 'End-to-end testing framework'),
('Jest', 'Testing', 'JavaScript testing framework'),
('Git', 'Version Control', 'Version control system'),
('CI/CD', 'DevOps', 'Continuous Integration/Deployment')
ON CONFLICT (name) DO NOTHING;

-- Insert default email templates
INSERT INTO email_templates (name, subject_template, html_template, text_template, variables, description) VALUES
(
    'daily_digest',
    'Your Daily Job Digest - {{digest_date}}',
    '<!DOCTYPE html><html><head><title>Daily Job Digest</title></head><body><h1>Your Daily Job Digest</h1><p>Hello {{user_name}},</p><p>Here are your job matches for {{digest_date}}:</p>{{#job_matches}}<div><h3>{{title}}</h3><p>{{company}} - {{location}}</p><p>Match Score: {{match_score}}%</p></div>{{/job_matches}}</body></html>',
    'Your Daily Job Digest\n\nHello {{user_name}},\n\nHere are your job matches for {{digest_date}}:\n\n{{#job_matches}}{{title}} at {{company}} ({{location}}) - Match: {{match_score}}%\n{{/job_matches}}',
    '["user_name", "digest_date", "job_matches"]',
    'Default daily digest email template'
),
(
    'weekly_digest',
    'Your Weekly Job Digest - {{digest_date}}',
    '<!DOCTYPE html><html><head><title>Weekly Job Digest</title></head><body><h1>Your Weekly Job Digest</h1><p>Hello {{user_name}},</p><p>Here is your weekly summary for {{digest_date}}:</p>{{#job_matches}}<div><h3>{{title}}</h3><p>{{company}} - {{location}}</p></div>{{/job_matches}}</body></html>',
    'Your Weekly Job Digest\n\nHello {{user_name}},\n\nHere is your weekly summary for {{digest_date}}:\n\n{{#job_matches}}{{title}} at {{company}} ({{location}})\n{{/job_matches}}',
    '["user_name", "digest_date", "job_matches"]',
    'Default weekly digest email template'
)
ON CONFLICT (name) DO NOTHING;

COMMIT; 
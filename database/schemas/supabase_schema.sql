
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    resume_text TEXT,
    resume_file_path VARCHAR(500),
    skills JSONB DEFAULT '[]',
    work_history JSONB DEFAULT '[]',
    education JSONB DEFAULT '[]',
    preferences JSONB DEFAULT '{}',
    linkedin_url VARCHAR(500),
    portfolio_url VARCHAR(500),
    phone VARCHAR(20),
    location VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Job searches table
CREATE TABLE IF NOT EXISTS job_searches (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    search_name VARCHAR(200) NOT NULL,
    job_titles JSONB DEFAULT '[]',
    locations JSONB DEFAULT '[]',
    keywords JSONB DEFAULT '[]',
    excluded_keywords JSONB DEFAULT '[]',
    remote_only BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Job search results table
CREATE TABLE IF NOT EXISTS job_search_results (
    id SERIAL PRIMARY KEY,
    job_search_id INTEGER NOT NULL REFERENCES job_searches(id) ON DELETE CASCADE,
    job_title VARCHAR(200) NOT NULL,
    company VARCHAR(200) NOT NULL,
    location VARCHAR(200) NOT NULL,
    url VARCHAR(500) NOT NULL,
    job_board VARCHAR(100) DEFAULT 'Ashby',
    posted_date VARCHAR(100),
    salary_range VARCHAR(200),
    job_type VARCHAR(100),
    remote_option VARCHAR(100),
    description_snippet TEXT,
    is_applied BOOLEAN DEFAULT FALSE,
    is_favorite BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Job applications table
CREATE TABLE IF NOT EXISTS job_applications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_result_id INTEGER REFERENCES job_search_results(id) ON DELETE SET NULL,
    job_url VARCHAR(500) NOT NULL,
    job_title VARCHAR(200) NOT NULL,
    company VARCHAR(200) NOT NULL,
    application_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'applied',
    notes TEXT,
    success BOOLEAN DEFAULT FALSE,
    filled_fields JSONB DEFAULT '[]',
    failed_fields JSONB DEFAULT '[]',
    error_message TEXT
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_job_searches_user_id ON job_searches(user_id);
CREATE INDEX IF NOT EXISTS idx_job_search_results_search_id ON job_search_results(job_search_id);
CREATE INDEX IF NOT EXISTS idx_job_applications_user_id ON job_applications(user_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_job_searches_updated_at BEFORE UPDATE ON job_searches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_searches ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_search_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_applications ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Users can only access their own data
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid()::text = id::text);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid()::text = id::text);

-- User profiles policies
CREATE POLICY "Users can view own profile data" ON user_profiles
    FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert own profile data" ON user_profiles
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update own profile data" ON user_profiles
    FOR UPDATE USING (auth.uid()::text = user_id::text);

-- Job searches policies
CREATE POLICY "Users can view own job searches" ON job_searches
    FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert own job searches" ON job_searches
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update own job searches" ON job_searches
    FOR UPDATE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can delete own job searches" ON job_searches
    FOR DELETE USING (auth.uid()::text = user_id::text);

-- Job search results policies
CREATE POLICY "Users can view own job search results" ON job_search_results
    FOR SELECT USING (
        job_search_id IN (
            SELECT id FROM job_searches WHERE user_id::text = auth.uid()::text
        )
    );

CREATE POLICY "Users can insert own job search results" ON job_search_results
    FOR INSERT WITH CHECK (
        job_search_id IN (
            SELECT id FROM job_searches WHERE user_id::text = auth.uid()::text
        )
    );

CREATE POLICY "Users can update own job search results" ON job_search_results
    FOR UPDATE USING (
        job_search_id IN (
            SELECT id FROM job_searches WHERE user_id::text = auth.uid()::text
        )
    );

-- Job applications policies
CREATE POLICY "Users can view own job applications" ON job_applications
    FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert own job applications" ON job_applications
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update own job applications" ON job_applications
    FOR UPDATE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can delete own job applications" ON job_applications
    FOR DELETE USING (auth.uid()::text = user_id::text);

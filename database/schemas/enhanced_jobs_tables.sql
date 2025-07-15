-- Enhanced Jobs Database Schema
-- This schema stores job positions with LLM-extracted structured data

-- Enhanced jobs table (extends the basic jobs table)
CREATE TABLE IF NOT EXISTS enhanced_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_job_id VARCHAR(255), -- Reference to original job
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    url TEXT NOT NULL,
    job_board VARCHAR(100),
    posted_date VARCHAR(100),
    job_type VARCHAR(50), -- 'full_time', 'part_time', 'contract', 'internship', 'freelance'
    remote_type VARCHAR(50), -- 'onsite', 'remote', 'hybrid', 'flexible'
    description_snippet TEXT,
    full_description TEXT,
    
    -- Extracted salary information
    salary_min_amount DECIMAL(12,2),
    salary_max_amount DECIMAL(12,2),
    salary_currency VARCHAR(10) DEFAULT 'USD',
    salary_type VARCHAR(50), -- 'annual', 'hourly', 'monthly', 'project_based'
    salary_negotiable BOOLEAN DEFAULT FALSE,
    salary_includes_equity BOOLEAN DEFAULT FALSE,
    salary_includes_benefits BOOLEAN DEFAULT FALSE,
    
    -- Extracted company information
    company_industry VARCHAR(255),
    company_size VARCHAR(255),
    company_founded_year INTEGER,
    company_headquarters VARCHAR(255),
    company_website VARCHAR(500),
    company_description TEXT,
    
    -- Extracted requirements
    required_skills TEXT[], -- Array of required skills
    preferred_skills TEXT[], -- Array of preferred skills
    required_experience_years INTEGER,
    experience_level VARCHAR(50), -- 'entry', 'junior', 'mid', 'senior', 'lead', 'principal', 'executive'
    required_education VARCHAR(255),
    required_certifications TEXT[],
    required_languages TEXT[],
    
    -- Extracted benefits
    benefits_health_insurance BOOLEAN DEFAULT FALSE,
    benefits_dental_insurance BOOLEAN DEFAULT FALSE,
    benefits_vision_insurance BOOLEAN DEFAULT FALSE,
    benefits_retirement_plan BOOLEAN DEFAULT FALSE,
    benefits_paid_time_off BOOLEAN DEFAULT FALSE,
    benefits_flexible_hours BOOLEAN DEFAULT FALSE,
    benefits_remote_work BOOLEAN DEFAULT FALSE,
    benefits_professional_development BOOLEAN DEFAULT FALSE,
    benefits_other TEXT[],
    
    -- Additional extracted fields
    responsibilities TEXT[],
    qualifications TEXT[],
    application_deadline TIMESTAMP WITH TIME ZONE,
    start_date TIMESTAMP WITH TIME ZONE,
    contract_duration VARCHAR(255),
    travel_requirements TEXT,
    visa_sponsorship BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    extraction_confidence DECIMAL(3,2) DEFAULT 0.0, -- 0.00 to 1.00
    extraction_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    raw_extraction_data JSONB, -- Raw LLM extraction output
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_enhanced_jobs_url ON enhanced_jobs(url);
CREATE INDEX IF NOT EXISTS idx_enhanced_jobs_company ON enhanced_jobs(company);
CREATE INDEX IF NOT EXISTS idx_enhanced_jobs_job_board ON enhanced_jobs(job_board);
CREATE INDEX IF NOT EXISTS idx_enhanced_jobs_job_type ON enhanced_jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_enhanced_jobs_remote_type ON enhanced_jobs(remote_type);
CREATE INDEX IF NOT EXISTS idx_enhanced_jobs_experience_level ON enhanced_jobs(experience_level);
CREATE INDEX IF NOT EXISTS idx_enhanced_jobs_salary_range ON enhanced_jobs(salary_min_amount, salary_max_amount);
CREATE INDEX IF NOT EXISTS idx_enhanced_jobs_extraction_confidence ON enhanced_jobs(extraction_confidence);
CREATE INDEX IF NOT EXISTS idx_enhanced_jobs_extraction_timestamp ON enhanced_jobs(extraction_timestamp);

-- Create GIN indexes for array fields
CREATE INDEX IF NOT EXISTS idx_enhanced_jobs_required_skills ON enhanced_jobs USING GIN(required_skills);
CREATE INDEX IF NOT EXISTS idx_enhanced_jobs_preferred_skills ON enhanced_jobs USING GIN(preferred_skills);
CREATE INDEX IF NOT EXISTS idx_enhanced_jobs_responsibilities ON enhanced_jobs USING GIN(responsibilities);
CREATE INDEX IF NOT EXISTS idx_enhanced_jobs_qualifications ON enhanced_jobs USING GIN(qualifications);

-- Create GIN index for JSONB field
CREATE INDEX IF NOT EXISTS idx_enhanced_jobs_raw_data ON enhanced_jobs USING GIN(raw_extraction_data);

-- Extraction statistics table
CREATE TABLE IF NOT EXISTS extraction_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    total_extractions INTEGER DEFAULT 0,
    successful_extractions INTEGER DEFAULT 0,
    failed_extractions INTEGER DEFAULT 0,
    average_confidence DECIMAL(3,2) DEFAULT 0.0,
    average_extraction_time DECIMAL(8,3) DEFAULT 0.0, -- seconds
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(date)
);

-- Extraction logs table for debugging and monitoring
CREATE TABLE IF NOT EXISTS extraction_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_url TEXT NOT NULL,
    extraction_status VARCHAR(50) NOT NULL, -- 'success', 'failed', 'partial'
    extraction_time DECIMAL(8,3), -- seconds
    confidence_score DECIMAL(3,2),
    error_message TEXT,
    llm_response TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for extraction logs
CREATE INDEX IF NOT EXISTS idx_extraction_logs_status ON extraction_logs(extraction_status);
CREATE INDEX IF NOT EXISTS idx_extraction_logs_created_at ON extraction_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_extraction_logs_confidence ON extraction_logs(confidence_score);

-- Extraction templates table
CREATE TABLE IF NOT EXISTS extraction_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    prompt_template TEXT NOT NULL,
    output_schema JSONB NOT NULL,
    version VARCHAR(50) DEFAULT '1.0',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create updated_at trigger function (if not exists)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_enhanced_jobs_updated_at BEFORE UPDATE ON enhanced_jobs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_extraction_templates_updated_at BEFORE UPDATE ON extraction_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default extraction template
INSERT INTO extraction_templates (name, description, prompt_template, output_schema) VALUES (
    'default_job_extraction',
    'Default template for extracting job information from descriptions',
    'You are an expert job description analyzer. Extract structured information from the following job posting.

Job Title: {job_title}
Company: {company_name}
URL: {job_url}

Job Description:
{job_description}

Please extract the following information in JSON format:

{
    "salary_info": {
        "min_amount": <number or null>,
        "max_amount": <number or null>,
        "currency": "USD",
        "salary_type": "annual|hourly|monthly|project_based",
        "is_negotiable": <boolean>,
        "includes_equity": <boolean>,
        "includes_benefits": <boolean>
    },
    "company_info": {
        "name": "<company name>",
        "industry": "<industry or null>",
        "size": "<company size or null>",
        "founded_year": <year or null>,
        "location": "<headquarters location or null>",
        "website": "<website or null>",
        "description": "<company description or null>"
    },
    "requirements": {
        "required_skills": ["<skill1>", "<skill2>"],
        "preferred_skills": ["<skill1>", "<skill2>"],
        "required_experience_years": <number or null>,
        "experience_level": "entry|junior|mid|senior|lead|principal|executive",
        "required_education": "<education level or null>",
        "certifications": ["<cert1>", "<cert2>"],
        "languages": ["<lang1>", "<lang2>"]
    },
    "benefits": {
        "health_insurance": <boolean>,
        "dental_insurance": <boolean>,
        "vision_insurance": <boolean>,
        "retirement_plan": <boolean>,
        "paid_time_off": <boolean>,
        "flexible_hours": <boolean>,
        "remote_work": <boolean>,
        "professional_development": <boolean>,
        "other_benefits": ["<benefit1>", "<benefit2>"]
    },
    "additional_info": {
        "responsibilities": ["<responsibility1>", "<responsibility2>"],
        "qualifications": ["<qualification1>", "<qualification2>"],
        "application_deadline": "<date or null>",
        "start_date": "<date or null>",
        "contract_duration": "<duration or null>",
        "travel_requirements": "<requirements or null>",
        "visa_sponsorship": <boolean>,
        "job_type": "full_time|part_time|contract|internship|freelance",
        "remote_type": "onsite|remote|hybrid|flexible"
    },
    "confidence_score": <float between 0 and 1>
}

Only include information that is explicitly mentioned in the job description. Use null for missing information. Be accurate and conservative in your extraction.',
    '{
        "type": "object",
        "properties": {
            "salary_info": {
                "type": "object",
                "properties": {
                    "min_amount": {"type": ["number", "null"]},
                    "max_amount": {"type": ["number", "null"]},
                    "currency": {"type": "string"},
                    "salary_type": {"type": "string", "enum": ["annual", "hourly", "monthly", "project_based"]},
                    "is_negotiable": {"type": "boolean"},
                    "includes_equity": {"type": "boolean"},
                    "includes_benefits": {"type": "boolean"}
                }
            },
            "company_info": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "industry": {"type": ["string", "null"]},
                    "size": {"type": ["string", "null"]},
                    "founded_year": {"type": ["integer", "null"]},
                    "location": {"type": ["string", "null"]},
                    "website": {"type": ["string", "null"]},
                    "description": {"type": ["string", "null"]}
                }
            },
            "requirements": {
                "type": "object",
                "properties": {
                    "required_skills": {"type": "array", "items": {"type": "string"}},
                    "preferred_skills": {"type": "array", "items": {"type": "string"}},
                    "required_experience_years": {"type": ["integer", "null"]},
                    "experience_level": {"type": "string", "enum": ["entry", "junior", "mid", "senior", "lead", "principal", "executive"]},
                    "required_education": {"type": ["string", "null"]},
                    "certifications": {"type": "array", "items": {"type": "string"}},
                    "languages": {"type": "array", "items": {"type": "string"}}
                }
            },
            "benefits": {
                "type": "object",
                "properties": {
                    "health_insurance": {"type": "boolean"},
                    "dental_insurance": {"type": "boolean"},
                    "vision_insurance": {"type": "boolean"},
                    "retirement_plan": {"type": "boolean"},
                    "paid_time_off": {"type": "boolean"},
                    "flexible_hours": {"type": "boolean"},
                    "remote_work": {"type": "boolean"},
                    "professional_development": {"type": "boolean"},
                    "other_benefits": {"type": "array", "items": {"type": "string"}}
                }
            },
            "additional_info": {
                "type": "object",
                "properties": {
                    "responsibilities": {"type": "array", "items": {"type": "string"}},
                    "qualifications": {"type": "array", "items": {"type": "string"}},
                    "application_deadline": {"type": ["string", "null"]},
                    "start_date": {"type": ["string", "null"]},
                    "contract_duration": {"type": ["string", "null"]},
                    "travel_requirements": {"type": ["string", "null"]},
                    "visa_sponsorship": {"type": "boolean"},
                    "job_type": {"type": "string", "enum": ["full_time", "part_time", "contract", "internship", "freelance"]},
                    "remote_type": {"type": "string", "enum": ["onsite", "remote", "hybrid", "flexible"]}
                }
            },
            "confidence_score": {"type": "number", "minimum": 0, "maximum": 1}
        }
    }'
) ON CONFLICT (name) DO NOTHING;

-- Create views for common queries
CREATE OR REPLACE VIEW enhanced_jobs_summary AS
SELECT 
    id,
    title,
    company,
    location,
    job_board,
    job_type,
    remote_type,
    salary_min_amount,
    salary_max_amount,
    salary_currency,
    experience_level,
    extraction_confidence,
    required_skills,
    preferred_skills,
    created_at
FROM enhanced_jobs
WHERE extraction_confidence > 0.5;

-- Create view for high-confidence extractions
CREATE OR REPLACE VIEW high_confidence_jobs AS
SELECT *
FROM enhanced_jobs
WHERE extraction_confidence >= 0.8
ORDER BY extraction_timestamp DESC;

-- Create view for salary analysis
CREATE OR REPLACE VIEW salary_analysis AS
SELECT 
    job_type,
    experience_level,
    remote_type,
    AVG(salary_min_amount) as avg_min_salary,
    AVG(salary_max_amount) as avg_max_salary,
    COUNT(*) as job_count
FROM enhanced_jobs
WHERE salary_min_amount IS NOT NULL 
  AND salary_max_amount IS NOT NULL
  AND extraction_confidence >= 0.7
GROUP BY job_type, experience_level, remote_type; 
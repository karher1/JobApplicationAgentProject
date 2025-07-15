-- Pending Applications System Schema
-- This schema supports human approval workflow for job applications

-- Create enum types for application status and priority
CREATE TYPE pending_application_status AS ENUM (
    'pending',
    'approved', 
    'rejected',
    'submitted',
    'failed',
    'cancelled'
);

CREATE TYPE pending_application_priority AS ENUM (
    'low',
    'medium',
    'high',
    'urgent'
);

-- Pending applications table
CREATE TABLE IF NOT EXISTS pending_applications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id VARCHAR(255) NOT NULL,
    job_title VARCHAR(200) NOT NULL,
    company VARCHAR(200) NOT NULL,
    job_url VARCHAR(500) NOT NULL,
    resume_id INTEGER REFERENCES resumes(id) ON DELETE SET NULL,
    cover_letter TEXT,
    form_data JSONB DEFAULT '{}',
    additional_info JSONB DEFAULT '{}',
    priority pending_application_priority DEFAULT 'medium',
    notes TEXT,
    status pending_application_status DEFAULT 'pending',
    
    -- Review tracking
    reviewed_at TIMESTAMP WITH TIME ZONE,
    reviewer_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    reviewer_notes TEXT,
    
    -- Submission tracking
    submitted_at TIMESTAMP WITH TIME ZONE,
    submission_result JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Application review log table (audit trail)
CREATE TABLE IF NOT EXISTS pending_application_reviews (
    id SERIAL PRIMARY KEY,
    application_id INTEGER NOT NULL REFERENCES pending_applications(id) ON DELETE CASCADE,
    reviewer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    old_status pending_application_status NOT NULL,
    new_status pending_application_status NOT NULL,
    reviewer_notes TEXT,
    modifications JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Application submission attempts table (for tracking retries)
CREATE TABLE IF NOT EXISTS pending_application_submissions (
    id SERIAL PRIMARY KEY,
    application_id INTEGER NOT NULL REFERENCES pending_applications(id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    success BOOLEAN NOT NULL DEFAULT false,
    filled_fields JSONB DEFAULT '[]',
    failed_fields JSONB DEFAULT '[]',
    error_message TEXT,
    submission_url VARCHAR(500),
    attempted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(application_id, attempt_number)
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_pending_applications_user_id ON pending_applications(user_id);
CREATE INDEX IF NOT EXISTS idx_pending_applications_status ON pending_applications(status);
CREATE INDEX IF NOT EXISTS idx_pending_applications_priority ON pending_applications(priority);
CREATE INDEX IF NOT EXISTS idx_pending_applications_created_at ON pending_applications(created_at);
CREATE INDEX IF NOT EXISTS idx_pending_applications_reviewer_id ON pending_applications(reviewer_id);
CREATE INDEX IF NOT EXISTS idx_pending_applications_job_id ON pending_applications(job_id);

CREATE INDEX IF NOT EXISTS idx_pending_application_reviews_application_id ON pending_application_reviews(application_id);
CREATE INDEX IF NOT EXISTS idx_pending_application_reviews_reviewer_id ON pending_application_reviews(reviewer_id);
CREATE INDEX IF NOT EXISTS idx_pending_application_reviews_created_at ON pending_application_reviews(created_at);

CREATE INDEX IF NOT EXISTS idx_pending_application_submissions_application_id ON pending_application_submissions(application_id);
CREATE INDEX IF NOT EXISTS idx_pending_application_submissions_attempted_at ON pending_application_submissions(attempted_at);

-- Create updated_at trigger for pending_applications
CREATE OR REPLACE FUNCTION update_pending_applications_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_pending_applications_updated_at
    BEFORE UPDATE ON pending_applications
    FOR EACH ROW
    EXECUTE FUNCTION update_pending_applications_updated_at();

-- Row Level Security (RLS) policies for pending applications
ALTER TABLE pending_applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE pending_application_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE pending_application_submissions ENABLE ROW LEVEL SECURITY;

-- Users can view/manage their own pending applications
CREATE POLICY "Users can view own pending applications" ON pending_applications
    FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert own pending applications" ON pending_applications
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update own pending applications" ON pending_applications
    FOR UPDATE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can delete own pending applications" ON pending_applications
    FOR DELETE USING (auth.uid()::text = user_id::text);

-- Reviewers can view and update applications (assume reviewer role is determined by business logic)
CREATE POLICY "Reviewers can view pending applications" ON pending_applications
    FOR SELECT USING (
        -- Allow users to see their own applications
        auth.uid()::text = user_id::text OR 
        -- Allow designated reviewers (this would need to be refined based on your role system)
        EXISTS (
            SELECT 1 FROM users 
            WHERE id::text = auth.uid()::text 
            AND (
                -- Add role-based conditions here
                email LIKE '%@admin.%' OR 
                email LIKE '%@manager.%'
            )
        )
    );

CREATE POLICY "Reviewers can update pending applications" ON pending_applications
    FOR UPDATE USING (
        -- Allow users to update their own applications (limited fields)
        auth.uid()::text = user_id::text OR 
        -- Allow reviewers to update any application
        EXISTS (
            SELECT 1 FROM users 
            WHERE id::text = auth.uid()::text 
            AND (
                -- Add role-based conditions here
                email LIKE '%@admin.%' OR 
                email LIKE '%@manager.%'
            )
        )
    );

-- Review log policies
CREATE POLICY "Users can view reviews of their applications" ON pending_application_reviews
    FOR SELECT USING (
        application_id IN (
            SELECT id FROM pending_applications 
            WHERE user_id::text = auth.uid()::text
        )
    );

CREATE POLICY "Reviewers can insert reviews" ON pending_application_reviews
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id::text = auth.uid()::text 
            AND (
                email LIKE '%@admin.%' OR 
                email LIKE '%@manager.%'
            )
        )
    );

-- Submission attempts policies
CREATE POLICY "Users can view submission attempts for their applications" ON pending_application_submissions
    FOR SELECT USING (
        application_id IN (
            SELECT id FROM pending_applications 
            WHERE user_id::text = auth.uid()::text
        )
    );

CREATE POLICY "System can insert submission attempts" ON pending_application_submissions
    FOR INSERT WITH CHECK (true);  -- System service can insert attempts

-- Helpful views for common queries
CREATE OR REPLACE VIEW pending_applications_summary AS
SELECT 
    pa.id,
    pa.user_id,
    pa.job_title,
    pa.company,
    pa.status,
    pa.priority,
    pa.created_at,
    pa.reviewed_at,
    pa.submitted_at,
    u.email as user_email,
    r.email as reviewer_email,
    (
        SELECT COUNT(*) 
        FROM pending_application_submissions pas 
        WHERE pas.application_id = pa.id
    ) as submission_attempts,
    (
        SELECT COUNT(*) 
        FROM pending_application_reviews par 
        WHERE par.application_id = pa.id
    ) as review_count
FROM pending_applications pa
LEFT JOIN users u ON pa.user_id = u.id
LEFT JOIN users r ON pa.reviewer_id = r.id;

-- View for reviewer dashboard
CREATE OR REPLACE VIEW pending_applications_for_review AS
SELECT 
    pa.*,
    u.email as user_email,
    u.first_name,
    u.last_name,
    r.name as resume_name,
    r.file_path as resume_file_path
FROM pending_applications pa
JOIN users u ON pa.user_id = u.id
LEFT JOIN resumes r ON pa.resume_id = r.id
WHERE pa.status = 'pending'
ORDER BY 
    CASE pa.priority
        WHEN 'urgent' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
    END,
    pa.created_at ASC;

-- View for user's application history
CREATE OR REPLACE VIEW user_application_history AS
SELECT 
    pa.id,
    pa.job_title,
    pa.company,
    pa.status,
    pa.priority,
    pa.created_at,
    pa.reviewed_at,
    pa.submitted_at,
    pa.reviewer_notes,
    CASE 
        WHEN pa.status = 'submitted' THEN 'Application submitted successfully'
        WHEN pa.status = 'approved' THEN 'Application approved, waiting for submission'
        WHEN pa.status = 'rejected' THEN 'Application rejected'
        WHEN pa.status = 'pending' THEN 'Application awaiting review'
        WHEN pa.status = 'failed' THEN 'Application submission failed'
        WHEN pa.status = 'cancelled' THEN 'Application cancelled'
    END as status_description,
    (
        SELECT COUNT(*) 
        FROM pending_application_submissions pas 
        WHERE pas.application_id = pa.id AND pas.success = true
    ) as successful_submissions
FROM pending_applications pa
ORDER BY pa.created_at DESC; 
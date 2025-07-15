-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Digest Templates Table
CREATE TABLE IF NOT EXISTS digest_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_type VARCHAR(50) NOT NULL CHECK (template_type IN ('daily', 'weekly', 'monthly', 'custom')),
    subject_template TEXT NOT NULL,
    html_template TEXT NOT NULL,
    text_template TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Digest Schedules Table
CREATE TABLE IF NOT EXISTS digest_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    digest_type VARCHAR(50) NOT NULL CHECK (digest_type IN ('daily', 'weekly', 'monthly', 'custom')),
    frequency VARCHAR(50) NOT NULL DEFAULT 'daily',
    preferred_time TIME DEFAULT '09:00:00',
    timezone VARCHAR(100) DEFAULT 'UTC',
    is_active BOOLEAN DEFAULT true,
    last_sent TIMESTAMP WITH TIME ZONE,
    next_scheduled TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, digest_type)
);

-- Digest Preferences Table
CREATE TABLE IF NOT EXISTS digest_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    include_job_matches BOOLEAN DEFAULT true,
    include_applications BOOLEAN DEFAULT true,
    include_insights BOOLEAN DEFAULT true,
    include_stats BOOLEAN DEFAULT true,
    max_job_matches INTEGER DEFAULT 10,
    max_application_updates INTEGER DEFAULT 20,
    preferred_job_types TEXT[],
    preferred_locations TEXT[],
    salary_range_min INTEGER,
    salary_range_max INTEGER,
    notification_frequency VARCHAR(50) DEFAULT 'daily',
    preferred_time TIME DEFAULT '09:00:00',
    timezone VARCHAR(100) DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Generated Digests Table
CREATE TABLE IF NOT EXISTS generated_digests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    digest_type VARCHAR(50) NOT NULL,
    digest_date DATE NOT NULL,
    content JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'generating', 'sent', 'failed')),
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    UNIQUE(user_id, digest_date, digest_type)
);

-- Notification Configurations Table
CREATE TABLE IF NOT EXISTS notification_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL CHECK (notification_type IN ('email', 'slack', 'webhook', 'sms')),
    email_address VARCHAR(255),
    slack_webhook TEXT,
    webhook_url TEXT,
    phone_number VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, notification_type)
);

-- Notification History Table
CREATE TABLE IF NOT EXISTS notification_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    digest_id UUID REFERENCES generated_digests(id) ON DELETE SET NULL,
    subject VARCHAR(500) NOT NULL,
    content_preview TEXT,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'sent' CHECK (status IN ('sent', 'delivered', 'failed', 'bounced')),
    error_message TEXT,
    delivery_time FLOAT,
    metadata JSONB DEFAULT '{}'
);

-- Email Templates Table
CREATE TABLE IF NOT EXISTS email_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    subject_template TEXT NOT NULL,
    html_template TEXT NOT NULL,
    text_template TEXT NOT NULL,
    variables TEXT[],
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Digest Statistics Table
CREATE TABLE IF NOT EXISTS digest_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE NOT NULL,
    total_digests_generated INTEGER DEFAULT 0,
    successful_digests INTEGER DEFAULT 0,
    failed_digests INTEGER DEFAULT 0,
    total_notifications_sent INTEGER DEFAULT 0,
    average_generation_time FLOAT DEFAULT 0,
    most_active_users JSONB DEFAULT '[]',
    digest_timeline JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(date)
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_digest_schedules_user_id ON digest_schedules(user_id);
CREATE INDEX IF NOT EXISTS idx_digest_schedules_next_scheduled ON digest_schedules(next_scheduled);
CREATE INDEX IF NOT EXISTS idx_generated_digests_user_date ON generated_digests(user_id, digest_date);
CREATE INDEX IF NOT EXISTS idx_generated_digests_status ON generated_digests(status);
CREATE INDEX IF NOT EXISTS idx_notification_history_user_id ON notification_history(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_history_sent_at ON notification_history(sent_at);
CREATE INDEX IF NOT EXISTS idx_digest_stats_date ON digest_stats(date);

-- Recommended RLS Policies (adjust as needed)
ALTER TABLE digest_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE digest_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_digests ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_history ENABLE ROW LEVEL SECURITY;

-- Example: Only allow users to access their own digest data
-- Note: Adjust these policies based on your authentication setup
-- If using Supabase Auth with UUID user IDs, use: user_id = auth.uid()
-- If using integer user IDs, use: user_id = (auth.uid()::text)::integer

-- For now, commenting out RLS policies - uncomment and adjust as needed
/*
CREATE POLICY "Users can view own digest schedules" ON digest_schedules
    FOR SELECT USING (user_id = (auth.uid()::text)::integer);

CREATE POLICY "Users can view own digest preferences" ON digest_preferences
    FOR SELECT USING (user_id = (auth.uid()::text)::integer);

CREATE POLICY "Users can view own generated digests" ON generated_digests
    FOR SELECT USING (user_id = (auth.uid()::text)::integer);

CREATE POLICY "Users can view own notification configs" ON notification_configs
    FOR SELECT USING (user_id = (auth.uid()::text)::integer);

CREATE POLICY "Users can view own notification history" ON notification_history
    FOR SELECT USING (user_id = (auth.uid()::text)::integer);
*/

-- (Add INSERT/UPDATE/DELETE policies as needed for your app's needs) 
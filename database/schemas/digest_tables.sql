-- Digest System Database Schema
-- This schema supports daily digest generation, email notifications, and user preferences

-- Digest Templates Table
CREATE TABLE IF NOT EXISTS digest_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    include_job_matches BOOLEAN DEFAULT true,
    include_applications BOOLEAN DEFAULT true,
    include_insights BOOLEAN DEFAULT true,
    include_stats BOOLEAN DEFAULT true,
    max_job_matches INTEGER DEFAULT 10,
    max_application_updates INTEGER DEFAULT 20,
    preferred_job_types TEXT[], -- Array of job types
    preferred_locations TEXT[], -- Array of locations
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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    digest_type VARCHAR(50) NOT NULL,
    digest_date DATE NOT NULL,
    content JSONB NOT NULL, -- Stores DigestContent as JSON
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'generating', 'sent', 'failed')),
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}', -- Additional metadata
    UNIQUE(user_id, digest_date, digest_type)
);

-- Notification Configurations Table
CREATE TABLE IF NOT EXISTS notification_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    digest_id UUID REFERENCES generated_digests(id) ON DELETE SET NULL,
    subject VARCHAR(500) NOT NULL,
    content_preview TEXT,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'sent' CHECK (status IN ('sent', 'delivered', 'failed', 'bounced')),
    error_message TEXT,
    delivery_time FLOAT, -- seconds
    metadata JSONB DEFAULT '{}'
);

-- Email Templates Table (for different notification types)
CREATE TABLE IF NOT EXISTS email_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    subject_template TEXT NOT NULL,
    html_template TEXT NOT NULL,
    text_template TEXT NOT NULL,
    variables TEXT[], -- Array of template variables
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Digest Statistics Table (for analytics)
CREATE TABLE IF NOT EXISTS digest_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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

-- Insert default email templates
INSERT INTO email_templates (name, subject_template, html_template, text_template, variables, description) VALUES
(
    'daily_digest',
    'Your Daily Job Digest - {{digest_date}}',
    '<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Job Digest</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #007bff; color: white; padding: 20px; text-align: center; }
        .section { margin: 20px 0; padding: 15px; border-left: 4px solid #007bff; }
        .job-match { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .match-score { color: #28a745; font-weight: bold; }
        .stats { background: #e9ecef; padding: 15px; border-radius: 5px; }
        .footer { text-align: center; margin-top: 30px; padding: 20px; background: #f8f9fa; }
        .btn { display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Your Daily Job Digest</h1>
            <p>{{digest_date}}</p>
        </div>
        
        {% if job_matches %}
        <div class="section">
            <h2>🎯 New Job Matches ({{job_matches|length}})</h2>
            {% for job in job_matches %}
            <div class="job-match">
                <h3>{{job.title}}</h3>
                <p><strong>{{job.company}}</strong> • {{job.location}}</p>
                <p class="match-score">Match Score: {{job.match_score}}%</p>
                <p><strong>Why it matches:</strong> {{job.match_reasons|join(", ")}}</p>
                {% if job.salary_range %}<p><strong>Salary:</strong> {{job.salary_range}}</p>{% endif %}
                <a href="{{job.application_url}}" class="btn">Apply Now</a>
            </div>
            {% endfor %}
        </div>
        {% endif %}
        
        {% if application_updates %}
        <div class="section">
            <h2>📋 Application Updates ({{application_updates|length}})</h2>
            {% for update in application_updates %}
            <div class="job-match">
                <h3>{{update.job_title}}</h3>
                <p><strong>{{update.company}}</strong></p>
                <p>Status: {{update.old_status}} → <strong>{{update.new_status}}</strong></p>
                <p>Updated: {{update.update_date}}</p>
                {% if update.notes %}<p><strong>Notes:</strong> {{update.notes}}</p>{% endif %}
            </div>
            {% endfor %}
        </div>
        {% endif %}
        
        {% if profile_insights %}
        <div class="section">
            <h2>💡 Profile Insights</h2>
            {% for insight in profile_insights %}
            <div class="job-match">
                <h3>{{insight.title}}</h3>
                <p>{{insight.description}}</p>
                <p><strong>Priority:</strong> {{insight.priority}}</p>
                {% if insight.action_required %}<p><strong>Action Required:</strong> Yes</p>{% endif %}
            </div>
            {% endfor %}
        </div>
        {% endif %}
        
        {% if system_stats %}
        <div class="stats">
            <h2>📊 Today''s Activity</h2>
            <p>• {{system_stats.new_jobs_found}} new jobs found</p>
            <p>• {{system_stats.applications_submitted}} applications submitted</p>
            <p>• {{system_stats.interviews_scheduled}} interviews scheduled</p>
            <p>• {{system_stats.skills_matched}} skills matched</p>
        </div>
        {% endif %}
        
        <div class="footer">
            <p><a href="{{dashboard_url}}">View Dashboard</a> | <a href="{{settings_url}}">Update Preferences</a></p>
            <p><a href="{{unsubscribe_url}}">Unsubscribe</a></p>
        </div>
    </div>
</body>
</html>',
    'Your Daily Job Digest - {{digest_date}}

{% if job_matches %}
NEW JOB MATCHES ({{job_matches|length}}):
{% for job in job_matches %}
- {{job.title}} at {{job.company}} ({{job.location}})
  Match Score: {{job.match_score}}%
  Why it matches: {{job.match_reasons|join(", ")}}
  {% if job.salary_range %}Salary: {{job.salary_range}}{% endif %}
  Apply: {{job.application_url}}

{% endfor %}
{% endif %}

{% if application_updates %}
APPLICATION UPDATES ({{application_updates|length}}):
{% for update in application_updates %}
- {{update.job_title}} at {{update.company}}
  Status: {{update.old_status}} → {{update.new_status}}
  Updated: {{update.update_date}}
  {% if update.notes %}Notes: {{update.notes}}{% endif %}

{% endfor %}
{% endif %}

{% if profile_insights %}
PROFILE INSIGHTS:
{% for insight in profile_insights %}
- {{insight.title}}: {{insight.description}}
  Priority: {{insight.priority}}
  {% if insight.action_required %}Action Required: Yes{% endif %}

{% endfor %}
{% endif %}

{% if system_stats %}
TODAY''S ACTIVITY:
- {{system_stats.new_jobs_found}} new jobs found
- {{system_stats.applications_submitted}} applications submitted
- {{system_stats.interviews_scheduled}} interviews scheduled
- {{system_stats.skills_matched}} skills matched
{% endif %}

Dashboard: {{dashboard_url}}
Settings: {{settings_url}}
Unsubscribe: {{unsubscribe_url}}',
    ARRAY['digest_date', 'job_matches', 'application_updates', 'profile_insights', 'system_stats', 'dashboard_url', 'settings_url', 'unsubscribe_url'],
    'Default template for daily digest emails'
),
(
    'weekly_digest',
    'Your Weekly Job Summary - {{digest_date}}',
    '<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weekly Job Summary</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #28a745; color: white; padding: 20px; text-align: center; }
        .section { margin: 20px 0; padding: 15px; border-left: 4px solid #28a745; }
        .summary-box { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .highlight { color: #28a745; font-weight: bold; }
        .footer { text-align: center; margin-top: 30px; padding: 20px; background: #f8f9fa; }
        .btn { display: inline-block; padding: 10px 20px; background: #28a745; color: white; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Your Weekly Job Summary</h1>
            <p>{{digest_date}}</p>
        </div>
        
        <div class="section">
            <h2>📈 Weekly Overview</h2>
            <div class="summary-box">
                <p><span class="highlight">{{system_stats.new_jobs_found}}</span> new jobs found</p>
                <p><span class="highlight">{{system_stats.applications_submitted}}</span> applications submitted</p>
                <p><span class="highlight">{{system_stats.interviews_scheduled}}</span> interviews scheduled</p>
                <p><span class="highlight">{{system_stats.offers_received}}</span> offers received</p>
            </div>
        </div>
        
        {% if top_skills %}
        <div class="section">
            <h2>🔥 Top Skills in Demand</h2>
            <p>{{top_skills|join(", ")}}</p>
        </div>
        {% endif %}
        
        {% if trending_companies %}
        <div class="section">
            <h2>🏢 Trending Companies</h2>
            <p>{{trending_companies|join(", ")}}</p>
        </div>
        {% endif %}
        
        <div class="footer">
            <p><a href="{{dashboard_url}}" class="btn">View Full Report</a></p>
            <p><a href="{{settings_url}}">Update Preferences</a> | <a href="{{unsubscribe_url}}">Unsubscribe</a></p>
        </div>
    </div>
</body>
</html>',
    'Your Weekly Job Summary - {{digest_date}}

WEEKLY OVERVIEW:
- {{system_stats.new_jobs_found}} new jobs found
- {{system_stats.applications_submitted}} applications submitted
- {{system_stats.interviews_scheduled}} interviews scheduled
- {{system_stats.offers_received}} offers received

{% if top_skills %}
TOP SKILLS IN DEMAND:
{{top_skills|join(", ")}}
{% endif %}

{% if trending_companies %}
TRENDING COMPANIES:
{{trending_companies|join(", ")}}
{% endif %}

View Full Report: {{dashboard_url}}
Settings: {{settings_url}}
Unsubscribe: {{unsubscribe_url}}',
    ARRAY['digest_date', 'system_stats', 'top_skills', 'trending_companies', 'dashboard_url', 'settings_url', 'unsubscribe_url'],
    'Template for weekly digest emails'
);

-- Insert default digest schedule for new users
CREATE OR REPLACE FUNCTION create_default_digest_schedule()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO digest_schedules (user_id, digest_type, frequency, preferred_time, timezone)
    VALUES (NEW.id, 'daily', 'daily', '09:00:00', 'UTC');
    
    INSERT INTO digest_preferences (user_id)
    VALUES (NEW.id);
    
    INSERT INTO notification_configs (user_id, notification_type, email_address)
    VALUES (NEW.id, 'email', NEW.email);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_create_default_digest_schedule
    AFTER INSERT ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION create_default_digest_schedule(); 
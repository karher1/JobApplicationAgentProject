-- Fixed jobs table that matches your existing schema
-- This assumes users.id is integer and job_searches.id is uuid

-- Drop the existing jobs table if it exists
DROP TABLE IF EXISTS public.jobs CASCADE;

-- Create the jobs table with correct foreign key types
CREATE TABLE public.jobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    search_id uuid REFERENCES public.job_searches(id) ON DELETE SET NULL,
    title text,
    company text,
    location text,
    url text,
    job_board text,
    posted_date text,
    salary_range text,
    job_type text,
    remote_option text,
    description_snippet text,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_jobs_search_id ON public.jobs(search_id);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON public.jobs(company);
CREATE INDEX IF NOT EXISTS idx_jobs_location ON public.jobs(location);
CREATE INDEX IF NOT EXISTS idx_jobs_job_board ON public.jobs(job_board);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON public.jobs(created_at);

-- Enable Row Level Security (RLS)
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (commented out - adjust based on your auth setup)
-- Policy: Users can view jobs
-- CREATE POLICY "Users can view jobs" ON public.jobs
--     FOR SELECT USING (true);

-- Policy: Users can insert jobs
-- CREATE POLICY "Users can insert jobs" ON public.jobs
--     FOR INSERT WITH CHECK (true);

-- Policy: Users can update jobs
-- CREATE POLICY "Users can update jobs" ON public.jobs
--     FOR UPDATE USING (true);

-- Policy: Users can delete jobs
-- CREATE POLICY "Users can delete jobs" ON public.jobs
--     FOR DELETE USING (true);

-- Add comments
COMMENT ON TABLE public.jobs IS 'Stores job postings from various job boards';
COMMENT ON COLUMN public.jobs.id IS 'Unique identifier for the job posting';
COMMENT ON COLUMN public.jobs.search_id IS 'Reference to the job search that found this job';
COMMENT ON COLUMN public.jobs.title IS 'Job title';
COMMENT ON COLUMN public.jobs.company IS 'Company name';
COMMENT ON COLUMN public.jobs.location IS 'Job location';
COMMENT ON COLUMN public.jobs.url IS 'URL to the job posting';
COMMENT ON COLUMN public.jobs.job_board IS 'Source job board (e.g., Ashby, Indeed)';
COMMENT ON COLUMN public.jobs.posted_date IS 'Date when job was posted';
COMMENT ON COLUMN public.jobs.salary_range IS 'Salary range if available';
COMMENT ON COLUMN public.jobs.job_type IS 'Type of job (full-time, part-time, contract)';
COMMENT ON COLUMN public.jobs.remote_option IS 'Remote work option (remote, hybrid, on-site)';
COMMENT ON COLUMN public.jobs.description_snippet IS 'Brief description or snippet from job posting'; 
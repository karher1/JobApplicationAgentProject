-- Add missing technologies_used column to work_experience table
ALTER TABLE work_experience 
ADD COLUMN IF NOT EXISTS technologies_used TEXT[] DEFAULT '{}';
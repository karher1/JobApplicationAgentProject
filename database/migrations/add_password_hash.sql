-- Add password_hash column to users table for authentication
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);

-- Create index on password_hash for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_password_hash ON users(password_hash);

-- Add comment to document the column
COMMENT ON COLUMN users.password_hash IS 'Hashed password for user authentication'; 
-- Add Korean title field to anime table
ALTER TABLE anime ADD COLUMN title_korean TEXT;

-- Create index for better search performance
CREATE INDEX IF NOT EXISTS idx_anime_title_korean ON anime(title_korean);

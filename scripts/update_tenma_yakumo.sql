-- Update Tenma and Yakumo character image paths to R2
UPDATE character SET image_url = '/images/characters/198.jpg' WHERE id = 198;
UPDATE character SET image_url = '/images/characters/202.jpg' WHERE id = 202;

-- Verify updates
SELECT id, name_full, image_url FROM character WHERE id IN (198, 202);

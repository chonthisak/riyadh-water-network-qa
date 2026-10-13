\set ON_ERROR_STOP on
BEGIN;
CREATE TABLE IF NOT EXISTS water_clean.pipes (LIKE water_raw.pipes INCLUDING ALL);
INSERT INTO water_clean.pipes SELECT * FROM water_raw.pipes ON CONFLICT(row_id) DO NOTHING;
-- These IDs are recovered from the synthetic specification, NOT inferred in real data.
INSERT INTO water_clean.repair_log VALUES
(1,'asset_id','DUP-ID','H00','Known ID from synthetic specification'),
(2,'asset_id','DUP-ID','H10','Known ID from synthetic specification')
ON CONFLICT DO NOTHING;
UPDATE water_clean.pipes SET asset_id='H00' WHERE row_id=1 AND asset_id='DUP-ID';
UPDATE water_clean.pipes SET asset_id='H10' WHERE row_id=2 AND asset_id='DUP-ID';
COMMIT;

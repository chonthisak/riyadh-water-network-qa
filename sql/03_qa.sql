\set ON_ERROR_STOP on
-- Use :pipe_table to evaluate raw or cleaned records.
-- Example: psql -v pipe_table=water_raw.pipes -f sql/03_qa.sql riyadh_portfolio
CREATE OR REPLACE VIEW water_qa.findings AS
WITH RECURSIVE
p AS (SELECT * FROM :pipe_table),
usable AS (SELECT * FROM p WHERE geom IS NOT NULL AND NOT ST_IsEmpty(geom) AND ST_IsValid(geom) AND ST_Length(geom)>0),
ends AS (SELECT row_id, ST_StartPoint(geom) a, ST_EndPoint(geom) b FROM usable),
edges AS (SELECT ST_AsEWKT(a) a, ST_AsEWKT(b) b FROM ends UNION SELECT ST_AsEWKT(b),ST_AsEWKT(a) FROM ends),
reachable(n) AS (
 SELECT ST_AsEWKT(geom) FROM water_raw.sources WHERE geom IS NOT NULL
 UNION SELECT e.b FROM edges e JOIN reachable r ON e.a=r.n
),
flags AS (
 SELECT 'MISSING_ID'::text code, 'pipes'::text layer,row_id,asset_id,'high'::text severity,'Required asset ID is missing'::text description,ST_StartPoint(geom) geom FROM p WHERE asset_id IS NULL OR btrim(asset_id)=''
 UNION ALL SELECT 'DUPLICATE_ID','pipes',row_id,asset_id,'high','Asset ID occurs more than once',ST_StartPoint(geom) FROM p WHERE asset_id IN (SELECT asset_id FROM p WHERE asset_id IS NOT NULL GROUP BY asset_id HAVING count(*)>1)
 UNION ALL SELECT 'MISSING_DIAMETER','pipes',row_id,asset_id,'high','Required diameter is missing',ST_StartPoint(geom) FROM p WHERE diameter_mm IS NULL
 UNION ALL SELECT 'INVALID_DIAMETER','pipes',row_id,asset_id,'high','Diameter must be positive',ST_StartPoint(geom) FROM p WHERE diameter_mm<=0
 UNION ALL SELECT 'EMPTY_GEOMETRY','pipes',row_id,asset_id,'high','Geometry is missing or empty',NULL::geometry FROM p WHERE geom IS NULL OR ST_IsEmpty(geom)
 UNION ALL SELECT 'INVALID_GEOMETRY','pipes',row_id,asset_id,'high',ST_IsValidReason(geom),ST_StartPoint(geom) FROM p WHERE geom IS NOT NULL AND NOT ST_IsEmpty(geom) AND NOT ST_IsValid(geom) AND ST_Length(geom)>0
 UNION ALL SELECT 'ZERO_LENGTH','pipes',row_id,asset_id,'high','Pipe has zero length',ST_StartPoint(geom) FROM p WHERE geom IS NOT NULL AND NOT ST_IsEmpty(geom) AND ST_Length(geom)=0
 UNION ALL SELECT 'DUPLICATE_GEOMETRY','pipes',q.row_id,q.asset_id,'high','Same line as an earlier row',ST_StartPoint(q.geom) FROM usable q WHERE EXISTS (SELECT 1 FROM usable p WHERE p.row_id<q.row_id AND ST_Equals(p.geom,q.geom))
 UNION ALL SELECT 'NEAR_GAP','pipes',q.row_id,pq.asset_id,'medium','Endpoint within 2 m of another pipe; review before snapping',q.a FROM ends p JOIN ends q ON p.row_id<q.row_id JOIN usable pq ON pq.row_id=q.row_id WHERE
 (ST_DWithin(p.a,q.a,2) AND NOT ST_Equals(p.a,q.a)) OR (ST_DWithin(p.a,q.b,2) AND NOT ST_Equals(p.a,q.b)) OR
 (ST_DWithin(p.b,q.a,2) AND NOT ST_Equals(p.b,q.a)) OR (ST_DWithin(p.b,q.b,2) AND NOT ST_Equals(p.b,q.b))
 UNION ALL SELECT 'DISCONNECTED','pipes',p.row_id,p.asset_id,'high','No endpoint path to a source',ST_StartPoint(p.geom) FROM usable p WHERE NOT EXISTS(SELECT 1 FROM reachable r WHERE r.n=ST_AsEWKT(ST_StartPoint(p.geom)))
 UNION ALL SELECT 'OFF_NETWORK_VALVE','valves',v.row_id,v.asset_id,'high','Valve farther than 2 m from every usable pipe',v.geom FROM water_raw.valves v WHERE NOT EXISTS(SELECT 1 FROM usable p WHERE ST_DWithin(v.geom,p.geom,2))
)
SELECT row_number() OVER(ORDER BY code,layer,row_id)::integer issue_id,* FROM flags;
SELECT code,count(*) AS findings FROM water_qa.findings GROUP BY code ORDER BY code;

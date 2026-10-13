# Case study: from raw records to reviewable GIS findings

## Business question
Which records need attention before an illustrative water network can support asset planning? A useful QA deliverable needs identifiable affected records, explainable rules, reproducible results and a clear distinction between confirmed repairs and review candidates.

## Method
Created a deterministic 34-pipe fixture in EPSG:32638 with seed 42. Internal keys remain unique while intentionally duplicated business IDs can be retained in staging. Stored raw and cleaned records separately. Evaluated attributes, length, duplicate geometry, 2-metre endpoint proximity, source reachability and valve placement. Exported all layers to one portable GeoPackage.

A recursive PostGIS query expresses the endpoint graph, while a standard-library Python implementation provides a small independent working demonstration. Exact coordinate equality defines junctions. A line crossing another line mid-span does not establish a connection. Spatial proximity flags review candidates rather than silently changing geometry.

## Findings and treatment
The Python run produced 11 findings. Two duplicate-ID findings were resolved by restoring H00 and H10 from the known fixture specification, reducing the count to 9. All geometric concerns remain for review. A missing or negative diameter needs an authoritative asset register; a near gap needs confirmation of intended connectivity; a disconnected branch may represent an omitted junction rather than a physical fault. No repair claims are made about the real Riyadh network.

## Verification
Seven tests passed: rule counts; exact affected records; a valid connected terminal/valve; a crossing that must remain disconnected; the 2 m boundary; repair geometry preservation; GeoPackage integrity, layer counts and SRID. Seeded defects are a regression fixture, not an estimate of performance on unseen real data. There is no measured precision/recall claim.

PostGIS execution was blocked by the sandbox's shared-memory restriction. The SQL implementation and result parity need local testing before describing the SQL workflow as production-ready. No hydraulic performance or pressure analysis is performed.

## Interview talking points
- Why staging permits duplicate business IDs while retaining unique row keys.
- Why coordinate reference systems and units affect tolerance rules.
- Why interior crossings and intentional dead ends need explicit semantics.
- Why repairing from authoritative data differs from guessing an ID or snapping a pipe.
- How a QA table can support a GIS editor's review queue.

## CV bullets
- Developed a reproducible synthetic GIS QA case study with QGIS-ready GeoPackage outputs, Python checks and a PostGIS SQL implementation.
- Identified 11 findings across 34 pipe records and documented two ID repairs while preserving unresolved geometry for review.
- Verified Python outputs and GeoPackage integrity with seven automated tests; documented outstanding local PostGIS validation.

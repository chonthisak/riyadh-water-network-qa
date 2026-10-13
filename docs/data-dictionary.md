# Data dictionary
All coordinates use WGS 84 / UTM zone 38N (EPSG:32638), metres. This is the appropriate UTM zone for Riyadh; positions are illustrative, not surveyed.

| Layer / field | Type | Meaning / rule |
|---|---|---|
| pipes.row_id | integer | Unique internal primary key |
| pipes.asset_id | text | Required business ID; must be unique in approved data |
| pipes.diameter_mm | integer | Required positive pipe diameter, millimetres |
| pipes.terminal_end | boolean | End is an intentional terminal; documentary field, not a topology exemption |
| pipes.geom | LineString | Nonempty positive-length pipe; two vertices in this fixture |
| valves / sources.row_id | integer | Unique internal key within layer |
| valves / sources.asset_id | text | Asset label |
| valves / sources.geom | Point | Valve location / supply origin |
| qa.issue_id | integer | Identifier within one run; not stable across reruns |
| qa.code | text | Rule identifier |
| qa.layer / row_id | text / integer | Together identify affected input record |
| qa.severity | text | high or medium; demonstration priorities |
| qa.description | text | Why a record needs attention |
| qa.geom | Point | Representative location; pipe start, not necessarily defect position |

Connectivity requires equal endpoint coordinates. Interior crossings do not form junctions, nor do endpoints within tolerance: these produce review flags. All interior junctions must be explicitly split into endpoints before using this model. A source must coincide with an endpoint. Intentional connected dead ends are accepted without a dangling-end flag. A near gap can still merit review at a declared terminal.

The Python checker supports the controlled two-vertex fixture with finite, nonempty coordinates; it is not a general geometry validator. The PostGIS workflow adds null/empty and invalid-geometry checks. Zero-length invalid lines receive ZERO_LENGTH rather than a second INVALID_GEOMETRY flag. SQL ST_Equals handles geometric equivalence beyond the Python check's forward/reversed vertex equality. Counts agree on the supplied fixture only after database validation.

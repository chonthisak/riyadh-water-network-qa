\set ON_ERROR_STOP on
CREATE EXTENSION IF NOT EXISTS postgis;
-- Run in a dedicated database. Existing project schemas are never dropped.
CREATE SCHEMA IF NOT EXISTS water_raw;
CREATE SCHEMA IF NOT EXISTS water_clean;
CREATE SCHEMA IF NOT EXISTS water_qa;
CREATE TABLE IF NOT EXISTS water_raw.pipes (
 row_id integer PRIMARY KEY, asset_id text, diameter_mm integer,
 terminal_end boolean NOT NULL DEFAULT false, geom geometry(LineString,32638));
CREATE TABLE IF NOT EXISTS water_raw.valves (row_id integer PRIMARY KEY, asset_id text, geom geometry(Point,32638));
CREATE TABLE IF NOT EXISTS water_raw.sources (row_id integer PRIMARY KEY, asset_id text, geom geometry(Point,32638));
CREATE INDEX IF NOT EXISTS pipes_geom_gix ON water_raw.pipes USING gist(geom);
CREATE INDEX IF NOT EXISTS valves_geom_gix ON water_raw.valves USING gist(geom);
CREATE INDEX IF NOT EXISTS sources_geom_gix ON water_raw.sources USING gist(geom);
CREATE TABLE IF NOT EXISTS water_clean.repair_log (
 row_id integer, field text, old_value text, new_value text, reason text,
 PRIMARY KEY(row_id,field));

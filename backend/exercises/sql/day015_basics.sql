-- PostgreSQL / psql：独立 atlas_course schema，不修改 public.devices。
\set ON_ERROR_STOP on
BEGIN;
CREATE SCHEMA IF NOT EXISTS atlas_course;
SET LOCAL search_path TO atlas_course;
CREATE TABLE IF NOT EXISTS users (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email text NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS devices (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL UNIQUE,
    device_type text NOT NULL CHECK (device_type IN ('router','switch','camera')),
    ip inet NOT NULL
);
CREATE TABLE IF NOT EXISTS alarms (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    device_id integer NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    level text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO users(email) VALUES ('learner@example.test') ON CONFLICT DO NOTHING;
INSERT INTO devices(name,device_type,ip) VALUES
 ('router-A','router','192.0.2.1'),
 ('switch-B','switch','192.0.2.2'),
 ('camera-C','camera','192.0.2.3') ON CONFLICT DO NOTHING;
SELECT id,name,ip FROM devices WHERE device_type='router' ORDER BY id LIMIT 10;
SAVEPOINT before_edit;
UPDATE devices SET name='temporary-name' WHERE name='camera-C';
DELETE FROM devices WHERE name='temporary-name';
ROLLBACK TO SAVEPOINT before_edit;
SELECT name FROM devices ORDER BY id; -- 三台仍然存在
COMMIT;

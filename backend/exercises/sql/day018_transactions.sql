\set ON_ERROR_STOP on
BEGIN;
SET LOCAL search_path TO atlas_course;
INSERT INTO devices(name,device_type,ip)
VALUES ('rollback-only','router','192.0.2.99');
SELECT name FROM devices WHERE name='rollback-only';
ROLLBACK;
SELECT count(*) AS should_be_zero FROM atlas_course.devices WHERE name='rollback-only';

-- PL/pgSQL 的 EXCEPTION 块建立子事务：内部任一步失败，块内写入一起回滚。
DO $$
DECLARE before_count bigint;
BEGIN
  SELECT count(*) INTO before_count FROM atlas_course.devices;
  BEGIN
    INSERT INTO atlas_course.devices(name,device_type,ip)
      VALUES ('rollback-on-failure','router','192.0.2.98');
    INSERT INTO atlas_course.alarms(device_id,level) VALUES (-999,'critical');
    RAISE EXCEPTION '预期外键错误却未发生';
  EXCEPTION WHEN foreign_key_violation THEN
    RAISE NOTICE '外键失败，块内设备 INSERT 也已回滚';
  END;
  IF (SELECT count(*) FROM atlas_course.devices) <> before_count THEN
    RAISE EXCEPTION '回滚验证失败';
  END IF;
END $$;

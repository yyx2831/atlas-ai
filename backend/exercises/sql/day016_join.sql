\set ON_ERROR_STOP on
BEGIN;
SET LOCAL search_path TO atlas_course;
-- 本课告警在事务结束全部回滚，可重复运行，不重复积累种子告警。
INSERT INTO alarms(device_id,level,created_at)
SELECT id,'critical',now()-interval '1 hour' FROM devices WHERE name='router-A';
INSERT INTO alarms(device_id,level,created_at)
SELECT id,'warning',now()-interval '2 hours' FROM devices WHERE name='router-A';
INSERT INTO alarms(device_id,level,created_at)
SELECT id,'warning',now()-interval '2 days' FROM devices WHERE name='switch-B';
SELECT d.name, count(a.id) AS alarm_count
FROM devices d LEFT JOIN alarms a
 ON a.device_id=d.id AND a.created_at >= now()-interval '24 hours'
GROUP BY d.id,d.name ORDER BY alarm_count DESC,d.id;
-- 首次 Day15 后预期 router-A=2，另外两台=0。
-- 对照：右表条件放在 WHERE，零匹配设备消失。
SELECT d.name, count(a.id) AS alarm_count
FROM devices d LEFT JOIN alarms a ON a.device_id=d.id
WHERE a.created_at >= now()-interval '24 hours'
GROUP BY d.id,d.name;
ROLLBACK;

\set ON_ERROR_STOP on
BEGIN;
-- 临时表会自动删除，不在真实 alarms 表上建删索引。
CREATE TEMP TABLE alarm_bench ON COMMIT DROP AS
SELECT g AS id,(g%100)+1 AS device_id,now()-g*interval '1 minute' AS created_at
FROM generate_series(1,100000) g;
ANALYZE alarm_bench;
EXPLAIN (ANALYZE,BUFFERS)
SELECT * FROM alarm_bench WHERE device_id=1 AND created_at>=now()-interval '24 hours';
CREATE INDEX ON alarm_bench(device_id,created_at);
ANALYZE alarm_bench;
EXPLAIN (ANALYZE,BUFFERS)
SELECT * FROM alarm_bench WHERE device_id=1 AND created_at>=now()-interval '24 hours';
-- 记录扫描方式、实际行数、buffers 与时间；缓存预热也会影响时间。
ROLLBACK;

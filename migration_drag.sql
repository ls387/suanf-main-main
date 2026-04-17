-- P2 手动拖拽调课：schedule_versions 加 parent_version_id 字段
-- 在开发数据库执行此语句后再启动后端

ALTER TABLE schedule_versions
  ADD COLUMN parent_version_id INT NULL COMMENT '来源版本ID（fork场景）',
  ADD CONSTRAINT fk_sv_parent
      FOREIGN KEY (parent_version_id)
      REFERENCES schedule_versions(version_id)
      ON DELETE SET NULL ON UPDATE CASCADE;

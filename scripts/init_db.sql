-- CodePractice OJ 平台数据库初始化脚本
-- 使用本机 root 账号执行（密码请替换为你的 root 密码）：
--   mysql -uroot -p < scripts/init_db.sql

CREATE DATABASE IF NOT EXISTS oj_platform
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- 创建专用账号（与 backend/.env 中的 DB_USER/DB_PASSWORD 保持一致）
CREATE USER IF NOT EXISTS 'oj'@'localhost' IDENTIFIED BY 'oj_pass_123';
CREATE USER IF NOT EXISTS 'oj'@'127.0.0.1' IDENTIFIED BY 'oj_pass_123';

GRANT ALL PRIVILEGES ON oj_platform.* TO 'oj'@'localhost';
GRANT ALL PRIVILEGES ON oj_platform.* TO 'oj'@'127.0.0.1';
FLUSH PRIVILEGES;

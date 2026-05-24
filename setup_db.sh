#!/bin/bash
# QMS 数据库初始化脚本
# 用法: bash setup_db.sh

set -e

echo "=========================================="
echo "  QMS 质量体系文件管理系统 - 数据库初始化"
echo "=========================================="

# 检查 PostgreSQL 是否在运行
if ! pg_isready -q 2>/dev/null; then
    echo "⚠️  PostgreSQL 未运行，正在启动..."
    sudo service postgresql start
    sleep 2
fi

echo "✅ PostgreSQL 运行中"

# 创建用户和数据库
sudo -u postgres psql <<EOF
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'qms_admin') THEN
        CREATE USER qms_admin WITH PASSWORD 'qms_123456';
    END IF;
END
\$\$;

SELECT 'CREATE DATABASE qms_db OWNER qms_admin'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'qms_db')\gexec

GRANT ALL PRIVILEGES ON DATABASE qms_db TO qms_admin;
EOF

echo "✅ 数据库用户 qms_admin 和数据库 qms_db 已就绪"

# 配置密码认证
PG_HBA=$(find /etc/postgresql -name pg_hba.conf 2>/dev/null | head -1)
if [ -n "$PG_HBA" ] && grep -q "local.*all.*all.*peer" "$PG_HBA"; then
    sudo sed -i 's/local\s\+all\s\+all\s\+peer/local   all             all                                     md5/' "$PG_HBA"
    sudo service postgresql restart
    echo "✅ 已启用密码认证，PostgreSQL 已重启"
fi

echo ""
echo "=========================================="
echo "  初始化完成！"
echo "  数据库: qms_db"
echo "  用户名: qms_admin"
echo "  密码:   qms_123456"
echo "=========================================="
echo ""
echo "启动应用:"
echo "  cd $(pwd)"
echo "  python3 -m venv venv"
echo "  source venv/bin/activate"
echo "  pip install -r requirements.txt"
echo "  python run.py"
echo "=========================================="

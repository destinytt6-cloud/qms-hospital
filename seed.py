"""初始化数据库 + 种子数据"""
import sys
import os

# 确保在项目根目录运行
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.database import init_db, SessionLocal
from app.models.department import Department
from app.models.document_category import DocumentCategory
from app.models.user import User


def seed():
    init_db()
    db = SessionLocal()

    try:
        # 1. 默认科室
        if not db.query(Department).first():
            depts = [
                Department(name="检验科", code="LAB", description="临床检验科"),
                Department(name="病理科", code="PATH", description="病理科"),
                Department(name="输血科", code="BB", description="输血科"),
                Department(name="质量管理科", code="QA", description="质量管理部门"),
                Department(name="院感科", code="IC", description="医院感染管理科"),
            ]
            db.add_all(depts)
            print("✅ 已创建默认科室")

        # 2. 默认文件分类（符合 ISO 15189 层级）
        if not db.query(DocumentCategory).first():
            cats = [
                DocumentCategory(name="质量手册", code="QM", description="质量方针与目标", sort_order=1),
                DocumentCategory(name="程序文件", code="SP", description="管理程序与技术程序", sort_order=2),
                DocumentCategory(name="作业指导书", code="SOP", description="标准操作流程", sort_order=3),
                DocumentCategory(name="记录表格", code="FR", description="质量与技术记录表单", sort_order=4),
                DocumentCategory(name="外来文件", code="EXT", description="法规、标准、指南等", sort_order=5),
                DocumentCategory(name="质量计划", code="QP", description="质量改进计划", sort_order=6),
            ]
            db.add_all(cats)
            print("✅ 已创建默认文件分类 (ISO 15189)")

        # 3. 默认管理员
        if not db.query(User).first():
            admin = User(
                username="admin",
                full_name="系统管理员",
                email="admin@hospital.com",
                role="admin",
                is_active=True,
            )
            admin.set_password("admin123")
            db.add(admin)
            print("✅ 已创建管理员: admin / admin123")

        db.commit()
        print("\n🎉 初始化完成!")
        print("   登录地址: http://localhost:8000")
        print("   用户名:   admin")
        print("   密码:     admin123")

    except Exception as e:
        db.rollback()
        print(f"❌ 初始化失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()

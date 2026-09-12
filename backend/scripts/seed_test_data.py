"""
测试数据生成脚本
用于创建分类、资源和联系方式的测试数据

仅用于 DEBUG 环境。非交互运行必须显式设置：
IBOOKS_TEST_DATA_CONFIRM=SEED_TEST_DATA
IBOOKS_TEST_ADMIN_PASSWORD=<non-production password>
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings  # noqa: E402
from app.database import AsyncSessionLocal  # noqa: E402
from app.models.category import Category  # noqa: E402
from app.models.contact import Contact  # noqa: E402
from app.models.resource import Resource  # noqa: E402
from app.models.user import User  # noqa: E402
from app.scripts.secure_inputs import read_secret, require_confirmation  # noqa: E402
from app.utils.security import get_password_hash  # noqa: E402


async def create_test_data():
    """创建测试数据"""
    if not settings.DEBUG:
        raise RuntimeError("Refusing to seed test data while DEBUG=false")

    require_confirmation(
        "IBOOKS_TEST_DATA_CONFIRM",
        expected="SEED_TEST_DATA",
        prompt="Type SEED_TEST_DATA to populate the current database: ",
    )
    test_admin_password = read_secret(
        "IBOOKS_TEST_ADMIN_PASSWORD",
        prompt="Test admin password: ",
        confirmation_prompt="Confirm test admin password: ",
    )

    async with AsyncSessionLocal() as session:
        try:
            # 1. 创建管理员用户
            print("📝 创建管理员用户...")
            from app.models.user import UserRole, UserStatus
            admin = User(
                email="admin@example.com",
                username="admin",
                password_hash=get_password_hash(test_admin_password),
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                is_email_verified=True
            )
            session.add(admin)
            await session.flush()
            print("✅ 管理员创建成功 - 邮箱: admin@example.com")
            print("   测试密码已安全提供，不会输出到终端。")

            # 2. 创建分类
            print("\n📚 创建分类...")
            categories_data = [
                {
                    "name": "编程开发",
                    "slug": "programming",
                    "description": "编程语言、框架和开发工具相关资源",
                    "icon": "💻"
                },
                {
                    "name": "UI/UX设计",
                    "slug": "design",
                    "description": "界面设计、用户体验和视觉设计资源",
                    "icon": "🎨"
                },
                {
                    "name": "数据科学",
                    "slug": "data-science",
                    "description": "机器学习、数据分析和人工智能资源",
                    "icon": "📊"
                },
                {
                    "name": "商业管理",
                    "slug": "business",
                    "description": "商业策略、管理和创业相关资源",
                    "icon": "💼"
                },
                {
                    "name": "个人成长",
                    "slug": "personal-growth",
                    "description": "自我提升、时间管理和效率工具",
                    "icon": "🌱"
                }
            ]

            categories = []
            for cat_data in categories_data:
                category = Category(**cat_data)
                session.add(category)
                categories.append(category)
            
            await session.flush()
            print(f"✅ 创建了 {len(categories)} 个分类")

            # 3. 创建资源
            print("\n📦 创建资源...")
            resources_data = [
                # 编程开发
                {
                    "title": "Python 完全指南 2024",
                    "slug": "python-complete-guide-2024",
                    "description": "从零基础到高级的 Python 编程完整教程，包含实战项目和最佳实践。这是一本全面的 Python 学习指南，涵盖基础语法、面向对象、Web开发、数据处理等内容。",
                    "excerpt": "从零基础到高级的 Python 编程完整教程",
                    "resource_type": "ebook",
                    "category_id": categories[0].id,
                    "price": 0,
                    "is_free": True,
                    "cloud_link": "https://pan.baidu.com/s/example1",
                    "access_code": "abc123",
                    "cover_image_url": "/images/python-guide.jpg",
                    "tags": ["Python", "编程", "入门"],
                    "is_featured": True,
                    "is_published": True,
                    "view_count": 1250,
                    "download_count": 380
                },
                {
                    "title": "React 18 实战开发",
                    "slug": "react-18-practical-development",
                    "description": "掌握 React 18 新特性，构建现代化 Web 应用。深入学习 React 18 的并发特性、Suspense、Server Components 等新功能。",
                    "excerpt": "掌握 React 18 新特性，构建现代化 Web 应用",
                    "resource_type": "video",
                    "category_id": categories[0].id,
                    "price": 0,
                    "is_free": True,
                    "cloud_link": "https://pan.baidu.com/s/example2",
                    "access_code": "xyz789",
                    "cover_image_url": "/images/react-course.jpg",
                    "tags": ["React", "前端", "JavaScript"],
                    "is_featured": True,
                    "is_published": True,
                    "view_count": 980,
                    "download_count": 245
                },
                {
                    "title": "Go 语言微服务实战",
                    "slug": "go-microservices-in-action",
                    "description": "使用 Go 语言构建高性能微服务架构。学习如何使用 Go 语言设计和实现可扩展的微服务系统。",
                    "excerpt": "使用 Go 语言构建高性能微服务架构",
                    "resource_type": "ebook",
                    "category_id": categories[0].id,
                    "price": 0,
                    "is_free": True,
                    "cloud_link": "https://pan.baidu.com/s/example3",
                    "access_code": "go2024",
                    "cover_image_url": "/images/go-microservices.jpg",
                    "tags": ["Go", "微服务", "后端"],
                    "is_featured": False,
                    "is_published": True,
                    "view_count": 567,
                    "download_count": 123
                },
                
                # UI/UX设计
                {
                    "title": "Figma 设计系统完全指南",
                    "slug": "figma-design-system-guide",
                    "description": "构建可扩展的设计系统，提升团队协作效率。从零开始构建企业级设计系统，包含组件库、设计规范和最佳实践。",
                    "excerpt": "构建可扩展的设计系统，提升团队协作效率",
                    "resource_type": "document",
                    "category_id": categories[1].id,
                    "price": 0,
                    "is_free": True,
                    "cloud_link": "https://pan.baidu.com/s/example4",
                    "access_code": "fig123",
                    "cover_image_url": "/images/figma-guide.jpg",
                    "tags": ["Figma", "设计系统", "UI"],
                    "is_featured": True,
                    "is_published": True,
                    "view_count": 834,
                    "download_count": 298
                },
                {
                    "title": "用户体验设计思维",
                    "slug": "ux-design-thinking",
                    "description": "掌握以用户为中心的设计方法论。学习用户研究、信息架构、交互设计和可用性测试的核心方法。",
                    "excerpt": "掌握以用户为中心的设计方法论",
                    "resource_type": "video",
                    "category_id": categories[1].id,
                    "price": 0,
                    "is_free": True,
                    "cloud_link": "https://pan.baidu.com/s/example5",
                    "access_code": "ux2024",
                    "cover_image_url": "/images/ux-thinking.jpg",
                    "tags": ["UX", "设计思维", "用户研究"],
                    "is_featured": False,
                    "is_published": True,
                    "view_count": 456,
                    "download_count": 167
                },
                
                # 数据科学
                {
                    "title": "机器学习实战项目集",
                    "slug": "machine-learning-projects",
                    "description": "10个真实项目带你掌握机器学习核心技能。包含图像识别、自然语言处理、推荐系统等实战项目。",
                    "excerpt": "10个真实项目带你掌握机器学习核心技能",
                    "resource_type": "ebook",
                    "category_id": categories[2].id,
                    "price": 0,
                    "is_free": True,
                    "cloud_link": "https://pan.baidu.com/s/example6",
                    "access_code": "ml2024",
                    "cover_image_url": "/images/ml-projects.jpg",
                    "tags": ["机器学习", "AI", "Python"],
                    "is_featured": True,
                    "is_published": True,
                    "view_count": 1456,
                    "download_count": 523
                },
                {
                    "title": "数据分析师必备技能",
                    "slug": "data-analyst-essential-skills",
                    "description": "SQL、Python、数据可视化全面掌握。系统学习数据分析的核心工具和方法，包含大量实战案例。",
                    "excerpt": "SQL、Python、数据可视化全面掌握",
                    "resource_type": "video",
                    "category_id": categories[2].id,
                    "price": 0,
                    "is_free": True,
                    "cloud_link": "https://pan.baidu.com/s/example7",
                    "access_code": "data99",
                    "cover_image_url": "/images/data-analyst.jpg",
                    "tags": ["数据分析", "SQL", "可视化"],
                    "is_featured": False,
                    "is_published": True,
                    "view_count": 723,
                    "download_count": 234
                },
                
                # 商业管理
                {
                    "title": "产品经理实战手册",
                    "slug": "product-manager-handbook",
                    "description": "从需求分析到产品上线的完整流程。涵盖产品规划、需求管理、项目协调和数据分析等核心技能。",
                    "excerpt": "从需求分析到产品上线的完整流程",
                    "resource_type": "ebook",
                    "category_id": categories[3].id,
                    "price": 0,
                    "is_free": True,
                    "cloud_link": "https://pan.baidu.com/s/example8",
                    "access_code": "pm2024",
                    "cover_image_url": "/images/pm-handbook.jpg",
                    "tags": ["产品经理", "需求分析", "项目管理"],
                    "is_featured": False,
                    "is_published": True,
                    "view_count": 645,
                    "download_count": 189
                },
                
                # 个人成长
                {
                    "title": "高效能人士的时间管理",
                    "slug": "time-management-for-professionals",
                    "description": "科学的时间管理方法，提升工作效率。学习番茄工作法、GTD、时间块等实用技巧。",
                    "excerpt": "科学的时间管理方法，提升工作效率",
                    "resource_type": "document",
                    "category_id": categories[4].id,
                    "price": 0,
                    "is_free": True,
                    "cloud_link": "https://pan.baidu.com/s/example9",
                    "access_code": "time88",
                    "cover_image_url": "/images/time-management.jpg",
                    "tags": ["时间管理", "效率", "个人成长"],
                    "is_featured": False,
                    "is_published": True,
                    "view_count": 892,
                    "download_count": 312
                }
            ]

            for res_data in resources_data:
                resource = Resource(**res_data)
                session.add(resource)
            
            print(f"✅ 创建了 {len(resources_data)} 个资源")

            # 4. 创建联系方式
            print("\n📞 创建联系方式...")
            from app.models.contact import ContactType
            
            contacts_data = [
                {
                    "type": ContactType.WECHAT,
                    "label": "微信号",
                    "value": "ibooks_support",
                    "is_copyable": True,
                    "is_active": True,
                    "display_order": 1,
                    "show_in_footer": True,
                    "show_in_contact_page": True
                },
                {
                    "type": ContactType.WECHAT_QR,
                    "label": "微信二维码",
                    "value": "扫码添加客服微信",
                    "qr_code_url": None,
                    "is_copyable": False,
                    "is_active": False,
                    "display_order": 2,
                    "show_in_footer": True,
                    "show_in_contact_page": True
                },
                {
                    "type": ContactType.QQ,
                    "label": "QQ号",
                    "value": "1234567890",
                    "is_copyable": True,
                    "is_clickable": True,
                    "link_url": "tencent://message/?uin=1234567890",
                    "is_active": True,
                    "display_order": 3,
                    "show_in_footer": True,
                    "show_in_contact_page": True
                },
                {
                    "type": ContactType.EMAIL,
                    "label": "邮箱",
                    "value": "support@ibooks.com",
                    "is_copyable": True,
                    "is_clickable": True,
                    "link_url": "mailto:support@ibooks.com",
                    "is_active": True,
                    "display_order": 4,
                    "show_in_footer": True,
                    "show_in_contact_page": True
                },
                {
                    "type": ContactType.TELEGRAM,
                    "label": "Telegram",
                    "value": "@ibooks_support",
                    "is_copyable": True,
                    "is_clickable": True,
                    "link_url": "https://t.me/ibooks_support",
                    "is_active": True,
                    "display_order": 5,
                    "show_in_footer": False,
                    "show_in_contact_page": True
                },
                {
                    "type": ContactType.BUSINESS_HOURS,
                    "label": "工作时间",
                    "value": "周一至周五 9:00-18:00",
                    "is_copyable": False,
                    "is_active": True,
                    "display_order": 6,
                    "show_in_footer": False,
                    "show_in_contact_page": True
                }
            ]
            
            for contact_data in contacts_data:
                contact = Contact(**contact_data)
                session.add(contact)
            
            print(f"✅ 创建了 {len(contacts_data)} 个联系方式")

            # 提交所有更改
            await session.commit()
            print("\n🎉 所有测试数据创建成功！")
            print("\n" + "="*50)
            print("📋 数据汇总:")
            print("  - 管理员账号: admin@example.com")
            print(f"  - 分类数量: {len(categories)}")
            print(f"  - 资源数量: {len(resources_data)}")
            print("  - 联系方式: 已配置")
            print("="*50)

        except Exception as e:
            await session.rollback()
            print(f"\n❌ 错误: {e}")
            raise


if __name__ == "__main__":
    print("🚀 开始创建测试数据...\n")
    asyncio.run(create_test_data())

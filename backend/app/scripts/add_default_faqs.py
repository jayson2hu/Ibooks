"""
Script to add default FAQ entries to the database.
"""
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import async_session
from app.models.faq import FAQ


async def add_default_faqs():
    """Add default FAQ entries."""
    
    default_faqs = [
        # 资源获取
        {
            "category": "资源获取",
            "question": "如何获取资源?",
            "answer": "浏览资源页面，找到您感兴趣的资源后，点击\"获取资源\"按钮即可查看云盘链接和提取码。部分资源可能需要登录后才能获取。",
            "display_order": 1,
        },
        {
            "category": "资源获取",
            "question": "资源链接失效怎么办?",
            "answer": "如果您发现资源链接失效，请通过联系我们页面报告问题，我们会尽快更新链接。建议您在获取资源后及时保存到自己的网盘。",
            "display_order": 2,
        },
        {
            "category": "资源获取",
            "question": "免费资源和付费资源有什么区别?",
            "answer": "免费资源可以直接获取，付费资源需要购买后才能查看下载链接。付费资源通常质量更高、内容更完整，并且会定期更新。",
            "display_order": 3,
        },
        
        # 账户问题
        {
            "category": "账户问题",
            "question": "如何注册账户?",
            "answer": "点击页面右上角的\"登录/注册\"按钮，填写邮箱、用户名和密码即可完成注册。注册后您可以收藏资源、查看下载历史等。",
            "display_order": 1,
        },
        {
            "category": "账户问题",
            "question": "忘记密码怎么办?",
            "answer": "在登录页面点击\"忘记密码\"，输入您的注册邮箱，我们会发送密码重置链接到您的邮箱。",
            "display_order": 2,
        },
        
        # 技术支持
        {
            "category": "技术支持",
            "question": "如何使用搜索功能?",
            "answer": "在页面顶部的搜索框中输入关键词，可以搜索资源标题、描述等内容。您还可以使用分类筛选来缩小搜索范围。",
            "display_order": 1,
        },
        {
            "category": "技术支持",
            "question": "支持哪些文件格式?",
            "answer": "我们支持各种常见格式，包括PDF、EPUB、MOBI（电子书）、MP4、AVI（视频）、ZIP、RAR（压缩包）等。具体支持的格式会在资源详情中说明。",
            "display_order": 2,
        },
        {
            "category": "技术支持",
            "question": "移动端可以使用吗?",
            "answer": "是的，我们的网站完全支持移动端浏览。您可以在手机或平板上访问，获得优化的移动浏览体验。",
            "display_order": 3,
        },
        
        # 支付相关
        {
            "category": "支付相关",
            "question": "支持哪些支付方式?",
            "answer": "我们支持微信支付、支付宝、银行卡等多种支付方式。具体支持的支付方式请在购买时查看。",
            "display_order": 1,
        },
        {
            "category": "支付相关",
            "question": "购买后可以退款吗?",
            "answer": "由于数字资源的特殊性，一旦您查看了下载链接，将无法退款。如果您在获取资源前遇到问题，可以联系客服处理。",
            "display_order": 2,
        },
        
        # 其他问题
        {
            "category": "其他问题",
            "question": "如何联系客服?",
            "answer": "您可以通过以下方式联系我们：\\n1. 访问\"联系我们\"页面查看联系方式\\n2. 发送邮件到客服邮箱\\n3. 添加客服微信或QQ\\n\\n我们的工作时间是周一至周日 9:00-21:00。",
            "display_order": 1,
        },
        {
            "category": "其他问题",
            "question": "资源会定期更新吗?",
            "answer": "是的，我们会持续添加新的优质资源，并定期检查和更新现有资源的链接。您可以关注我们的更新动态。",
            "display_order": 2,
        },
    ]
    
    async with async_session() as session:
        try:
            for faq_data in default_faqs:
                faq = FAQ(**faq_data)
                session.add(faq)
            
            await session.commit()
            print(f"Successfully added {len(default_faqs)} FAQ entries!")
            
        except Exception as e:
            await session.rollback()
            print(f"Error adding FAQs: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(add_default_faqs())

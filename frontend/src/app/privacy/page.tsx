import Link from 'next/link';

export default function PrivacyPage() {
    return (
        <div className="min-h-screen pt-24">
            <div className="container max-w-3xl py-10">
                <h1 className="text-3xl font-bold text-gray-900 mb-6">隐私政策</h1>
                <div className="space-y-5 text-gray-700 leading-7">
                    <p>我们只在提供账户、资源交付、订单和客户支持所必需的范围内处理信息。</p>
                    <p>账户信息用于登录、邮箱验证和安全通知；订单与书币流水用于完成购买、退款和审计。我们不会出售个人信息。</p>
                    <p>如需查询、更正或删除账户信息，请通过联系方式页面联系我们。</p>
                </div>
                <Link href="/contact" className="mt-8 inline-block text-blue-600 hover:text-blue-700">前往联系方式</Link>
            </div>
        </div>
    );
}

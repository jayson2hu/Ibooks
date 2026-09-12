import Link from 'next/link';

export default function TermsPage() {
    return (
        <div className="min-h-screen pt-24">
            <div className="container max-w-3xl py-10">
                <h1 className="text-3xl font-bold text-gray-900 mb-6">服务条款</h1>
                <div className="space-y-5 text-gray-700 leading-7">
                    <p>用户应使用真实、合法的信息注册账户，并妥善保管登录凭据。</p>
                    <p>资源仅限购买账户本人在合法范围内使用。禁止转售、公开传播或以其他方式侵犯权利人的权益。</p>
                    <p>书币充值、资源购买和访问权限以平台记录为准；遇到订单或交付问题，请及时联系我们处理。</p>
                </div>
                <Link href="/contact" className="mt-8 inline-block text-blue-600 hover:text-blue-700">前往联系方式</Link>
            </div>
        </div>
    );
}

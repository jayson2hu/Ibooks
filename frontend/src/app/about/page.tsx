export default function AboutPage() {
    return (
        <div className="min-h-screen pt-20">
            <div className="container py-8">
                {/* Header */}
                <div className="text-center mb-12">
                    <h1 className="text-4xl font-bold mb-4">关于我们</h1>
                    <p className="text-xl text-secondary">
                        致力于提供优质的数字资源服务
                    </p>
                </div>

                {/* Content */}
                <div className="max-w-4xl mx-auto space-y-8">
                    {/* Introduction */}
                    <div className="card">
                        <h2 className="text-2xl font-bold mb-4">我们是谁</h2>
                        <p className="text-secondary mb-4">
                            我们是一个专注于数字资源分享的平台，致力于为用户提供高质量的电子书、视频课程、技术文档等数字内容。
                        </p>
                        <p className="text-secondary">
                            通过精心筛选和整理，我们确保每一份资源都具有学习价值，帮助用户快速获取所需知识。
                        </p>
                    </div>

                    {/* Mission */}
                    <div className="card gradient-primary text-white">
                        <h2 className="text-2xl font-bold mb-4">我们的使命</h2>
                        <p className="text-white/90 mb-4">
                            让优质的数字资源触手可及，降低知识获取的门槛，帮助更多人实现终身学习的目标。
                        </p>
                        <ul className="space-y-2 text-white/90">
                            <li>✅ 提供高质量、多样化的数字资源</li>
                            <li>✅ 确保资源的可靠性和安全性</li>
                            <li>✅ 优化用户体验，简化获取流程</li>
                            <li>✅ 持续更新，跟进最新技术趋势</li>
                        </ul>
                    </div>

                    {/* Values */}
                    <div className="grid grid-2 gap-6">
                        <div className="card text-center">
                            <div className="text-4xl mb-4">🎯</div>
                            <h3 className="text-xl font-semibold mb-2">精选内容</h3>
                            <p className="text-secondary">
                                我们只提供经过验证的高质量资源
                            </p>
                        </div>
                        <div className="card text-center">
                            <div className="text-4xl mb-4">⚡</div>
                            <h3 className="text-xl font-semibold mb-2">快速交付</h3>
                            <p className="text-secondary">
                                云盘直链，无需等待，即刻获取
                            </p>
                        </div>
                        <div className="card text-center">
                            <div className="text-4xl mb-4">🔒</div>
                            <h3 className="text-xl font-semibold mb-2">安全可靠</h3>
                            <p className="text-secondary">
                                所有资源经过安全检查，放心使用
                            </p>
                        </div>
                        <div className="card text-center">
                            <div className="text-4xl mb-4">💡</div>
                            <h3 className="text-xl font-semibold mb-2">持续更新</h3>
                            <p className="text-secondary">
                                定期更新资源库，紧跟行业前沿
                            </p>
                        </div>
                    </div>

                    {/* Contact CTA */}
                    <div className="card bg-surface text-center">
                        <h2 className="text-2xl font-bold mb-4">联系我们</h2>
                        <p className="text-secondary mb-6">
                            如有任何问题或建议，欢迎随时与我们联系
                        </p>
                        <a href="/contact" className="btn btn-primary">
                            查看联系方式
                        </a>
                    </div>
                </div>
            </div>
        </div>
    );
}

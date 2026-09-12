'use client';

interface CategoryDetailErrorProps {
    error: Error & { digest?: string };
    reset: () => void;
}

export default function CategoryDetailError({ reset }: CategoryDetailErrorProps) {
    return (
        <main className="min-h-screen pt-20">
            <div className="container py-16">
                <div role="alert" className="mx-auto max-w-xl rounded-xl border border-red-200 bg-red-50 p-8 text-center">
                    <h1 className="text-2xl font-bold text-gray-900">分类详情加载失败</h1>
                    <p className="mt-3 text-red-700">服务暂时不可用，请稍后重试。</p>
                    <button
                        type="button"
                        onClick={reset}
                        className="mt-6 rounded-lg bg-primary px-5 py-2.5 font-medium text-white hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                    >
                        重新加载
                    </button>
                </div>
            </div>
        </main>
    );
}

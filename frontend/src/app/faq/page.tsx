import { api } from '@/lib/api';
import type { Metadata } from 'next';
import {
    QuestionMarkCircleIcon,
    ChevronDownIcon
} from '@heroicons/react/24/outline';
import RetryableError from '@/components/common/RetryableError';

export const metadata: Metadata = {
    title: '常见问题 - FAQ',
    description: '常见问题解答 - 帮助您快速找到答案',
};

export const dynamic = 'force-dynamic';

interface FAQ {
    id: number;
    category: string;
    question: string;
    answer: string;
    display_order: number;
    is_active: boolean;
}

export default async function FAQPage() {
    let faqs: FAQ[] = [];
    let loadFailed = false;

    try {
        const response = await api.faqs.list(true);
        faqs = response.data || [];
    } catch (error) {
        console.error('Failed to fetch FAQs:', error);
        loadFailed = true;
    }

    // Group FAQs by category
    const groupedFAQs: Record<string, FAQ[]> = {};
    faqs.forEach(faq => {
        if (!groupedFAQs[faq.category]) {
            groupedFAQs[faq.category] = [];
        }
        groupedFAQs[faq.category].push(faq);
    });

    // Sort FAQs within each category
    Object.keys(groupedFAQs).forEach(category => {
        groupedFAQs[category].sort((a, b) => a.display_order - b.display_order);
    });

    return (
        <div className="min-h-screen pt-20 bg-gradient-to-br from-gray-50 to-blue-50/30">
            <div className="container mx-auto px-4 py-12">
                {/* Header */}
                <div className="text-center mb-12">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full mb-4">
                        <QuestionMarkCircleIcon className="w-10 h-10 text-white" />
                    </div>
                    <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
                        常见问题
                    </h1>
                    <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                        我们整理了常见问题的解答，帮助您快速找到答案
                    </p>
                </div>

                {/* FAQ Content */}
                <div className="max-w-4xl mx-auto">
                    {loadFailed ? (
                        <RetryableError message="常见问题加载失败，请稍后重试。" />
                    ) : faqs.length === 0 ? (
                        <div className="text-center py-20">
                            <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full mb-4">
                                <QuestionMarkCircleIcon className="w-8 h-8 text-gray-400" />
                            </div>
                            <p className="text-gray-500">暂无常见问题</p>
                        </div>
                    ) : (
                        <div className="space-y-8">
                            {Object.entries(groupedFAQs).map(([category, categoryFAQs]) => (
                                <div key={category} className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                                    <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-4">
                                        <h2 className="text-xl font-bold text-white">{category}</h2>
                                    </div>

                                    <div className="divide-y divide-gray-100">
                                        {categoryFAQs.map((faq) => (
                                            <details key={faq.id} className="group">
                                                <summary className="flex items-start justify-between gap-4 px-6 py-5 cursor-pointer hover:bg-gray-50 transition-colors">
                                                    <div className="flex items-start gap-3 flex-1">
                                                        <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center shrink-0 mt-0.5 font-semibold text-sm">
                                                            Q
                                                        </div>
                                                        <h3 className="text-lg font-medium text-gray-800 group-open:text-blue-600 transition-colors">
                                                            {faq.question}
                                                        </h3>
                                                    </div>
                                                    <ChevronDownIcon className="w-5 h-5 text-gray-400 group-open:rotate-180 transition-transform shrink-0 mt-1" />
                                                </summary>

                                                <div className="px-6 pb-5 pl-[52px]">
                                                    <div className="prose prose-blue max-w-none">
                                                        <div className="text-gray-600 whitespace-pre-wrap">{faq.answer}</div>
                                                    </div>
                                                </div>
                                            </details>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Contact CTA */}
                <div className="max-w-4xl mx-auto mt-12 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-8 text-center text-white shadow-lg">
                    <h2 className="text-2xl font-bold mb-2">没有找到您的问题?</h2>
                    <p className="mb-6 text-blue-100">我们的客服团队随时准备帮助您</p>
                    <a
                        href="/contact"
                        className="inline-block px-8 py-3 bg-white text-blue-600 rounded-lg font-semibold hover:bg-gray-50 transition-colors shadow-lg"
                    >
                        联系我们
                    </a>
                </div>
            </div>
        </div>
    );
}

'use client';

import { useRouter } from 'next/navigation';

interface RetryableErrorProps {
    message: string;
    onRetry?: () => void;
}

export default function RetryableError({ message, onRetry }: RetryableErrorProps) {
    const router = useRouter();

    return (
        <div
            role="alert"
            className="rounded-xl border border-red-200 bg-red-50 px-5 py-4 text-center text-red-700"
        >
            <p>{message}</p>
            <button
                type="button"
                className="mt-3 font-medium text-red-800 underline underline-offset-4 hover:text-red-950"
                onClick={onRetry ?? (() => router.refresh())}
            >
                重新加载
            </button>
        </div>
    );
}

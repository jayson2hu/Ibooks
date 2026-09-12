'use client';

import { useState } from 'react';

export default function ShareButton({ title }: { title: string }) {
    const [feedback, setFeedback] = useState('');

    const share = async () => {
        const url = window.location.href;
        setFeedback('');

        try {
            if (navigator.share) {
                await navigator.share({ title, url });
                setFeedback('分享面板已打开');
                return;
            }

            if (navigator.clipboard?.writeText) {
                await navigator.clipboard.writeText(url);
                setFeedback('链接已复制');
                return;
            }

            setFeedback('当前浏览器不支持自动分享，请复制地址栏链接。');
        } catch (error) {
            if (error instanceof DOMException && error.name === 'AbortError') {
                return;
            }
            setFeedback('分享失败，请稍后重试。');
        }
    };

    return (
        <div>
            <button type="button" className="btn btn-secondary w-full" onClick={share}>
                分享
            </button>
            <p className="mt-2 min-h-5 text-center text-xs text-tertiary" aria-live="polite">
                {feedback}
            </p>
        </div>
    );
}

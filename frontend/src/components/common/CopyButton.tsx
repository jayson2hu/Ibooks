'use client';

import { useState } from 'react';

interface CopyButtonProps {
    value: string;
    className?: string;
    label?: string | React.ReactNode;
}

export default function CopyButton({ value, className, label }: CopyButtonProps) {
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(value);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy text: ', err);
        }
    };

    if (label) {
        return (
            <button
                onClick={handleCopy}
                className={className}
                title={copied ? "已复制" : "点击复制"}
            >
                {copied ? <span className="text-green-600">已复制</span> : label}
            </button>
        )
    }

    return (
        <button
            onClick={handleCopy}
            className={className}
            title={copied ? "已复制" : "复制"}
        >
            {copied ? '✅' : '📋'}
        </button>
    );
}

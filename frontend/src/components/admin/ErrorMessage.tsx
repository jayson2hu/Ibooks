interface ErrorMessageProps {
    message: string;
    onRetry?: () => void;
}

export default function ErrorMessage({ message, onRetry }: ErrorMessageProps) {
    return (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
            <div className="flex items-start">
                <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                </div>
                <div className="ml-3 flex-1">
                    <h3 className="text-sm font-medium text-red-800">加载数据时出错</h3>
                    <p className="mt-1 text-sm text-red-700">{message}</p>
                    {onRetry && (
                        <button
                            onClick={onRetry}
                            className="mt-3 px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 transition-colors"
                        >
                            重试
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}

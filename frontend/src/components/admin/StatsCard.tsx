interface StatsCardProps {
    title: string;
    value: string | number;
    change?: string;
    changeType?: 'increase' | 'decrease';
    icon: React.ReactNode;
    iconBg: string;
}

export default function StatsCard({
    title,
    value,
    change,
    changeType = 'increase',
    icon,
    iconBg
}: StatsCardProps) {
    return (
        <div className="group bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-xl hover:border-gray-300 transition-all duration-300 hover:-translate-y-1">
            <div className="flex items-center justify-between">
                <div className="flex-1">
                    <p className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">{title}</p>
                    <h3 className="text-3xl font-bold text-gray-900 mb-1">{value}</h3>
                    {change && (
                        <p className="mt-2 text-sm flex items-center">
                            <span className={`font-semibold flex items-center ${changeType === 'increase' ? 'text-green-600' : 'text-red-600'
                                }`}>
                                {changeType === 'increase' ? (
                                    <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                                    </svg>
                                ) : (
                                    <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                    </svg>
                                )}
                                {change}
                            </span>
                            <span className="text-gray-500 ml-1.5">vs 上月</span>
                        </p>
                    )}
                </div>
                <div className={`w-16 h-16 ${iconBg} rounded-2xl flex items-center justify-center text-3xl shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                    {icon}
                </div>
            </div>
        </div>
    );
}

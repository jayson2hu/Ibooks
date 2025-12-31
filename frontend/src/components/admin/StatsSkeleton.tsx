export default function StatsSkeleton() {
    return (
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 animate-pulse">
            <div className="flex items-center justify-between">
                <div className="flex-1">
                    <div className="h-4 bg-gray-200 rounded w-24 mb-3"></div>
                    <div className="h-8 bg-gray-200 rounded w-32 mb-3"></div>
                    <div className="h-3 bg-gray-200 rounded w-28"></div>
                </div>
                <div className="w-14 h-14 bg-gray-200 rounded-xl"></div>
            </div>
        </div>
    );
}

'use client';

import { motion } from 'framer-motion';

interface SkeletonLoaderProps {
  type: 'card' | 'text' | 'image';
  count?: number;
}

const SkeletonCard = () => (
  <div className="bg-white rounded-xl overflow-hidden shadow-md border border-gray-100">
    {/* 图片骨架 */}
    <div className="aspect-[4/3] bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 animate-shimmer bg-[length:200%_100%]" />

    {/* 内容骨架 */}
    <div className="p-4 space-y-3">
      {/* 标签 */}
      <div className="h-6 w-20 bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 animate-shimmer bg-[length:200%_100%] rounded-md" />

      {/* 标题 */}
      <div className="space-y-2">
        <div className="h-4 bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 animate-shimmer bg-[length:200%_100%] rounded" />
        <div className="h-4 w-3/4 bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 animate-shimmer bg-[length:200%_100%] rounded" />
      </div>

      {/* 描述 */}
      <div className="space-y-2">
        <div className="h-3 bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 animate-shimmer bg-[length:200%_100%] rounded" />
        <div className="h-3 w-5/6 bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 animate-shimmer bg-[length:200%_100%] rounded" />
      </div>

      {/* 元信息 */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100">
        <div className="h-3 w-16 bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 animate-shimmer bg-[length:200%_100%] rounded" />
        <div className="h-3 w-12 bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 animate-shimmer bg-[length:200%_100%] rounded" />
      </div>
    </div>
  </div>
);

const SkeletonText = () => (
  <div className="space-y-2">
    <div className="h-4 bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 animate-shimmer bg-[length:200%_100%] rounded w-full" />
    <div className="h-4 bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 animate-shimmer bg-[length:200%_100%] rounded w-5/6" />
    <div className="h-4 bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 animate-shimmer bg-[length:200%_100%] rounded w-4/6" />
  </div>
);

const SkeletonImage = () => (
  <div className="aspect-video bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 animate-shimmer bg-[length:200%_100%] rounded-lg" />
);

export default function SkeletonLoader({ type, count = 1 }: SkeletonLoaderProps) {
  const renderSkeleton = () => {
    switch (type) {
      case 'card':
        return <SkeletonCard />;
      case 'text':
        return <SkeletonText />;
      case 'image':
        return <SkeletonImage />;
      default:
        return <SkeletonCard />;
    }
  };

  return (
    <>
      {Array.from({ length: count }).map((_, index) => (
        <motion.div
          key={index}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3, delay: index * 0.05 }}
        >
          {renderSkeleton()}
        </motion.div>
      ))}
    </>
  );
}

// 资源网格骨架屏
export function ResourceGridSkeleton({ count = 10 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
      <SkeletonLoader type="card" count={count} />
    </div>
  );
}

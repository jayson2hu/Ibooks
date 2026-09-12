'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { CalendarIcon, HeartIcon } from '@heroicons/react/24/outline';
import { HeartIcon as HeartSolidIcon } from '@heroicons/react/24/solid';
import { useState } from 'react';
import ResourceCover from '@/components/common/ResourceCover';

interface Resource {
  id: number;
  title: string;
  description?: string;
  slug: string;
  resource_type: string;
  price: number;
  coin_price?: number;
  is_free: boolean;
  cover_image_url?: string;
  created_at?: string;
  likes_count?: number;
  view_count?: number;
}

interface ResourceCardProps {
  resource: Resource;
  onHover?: (id: number) => void;
}

export default function ResourceCard({ resource, onHover }: ResourceCardProps) {
  const [isLiked, setIsLiked] = useState(false);

  const formatDate = (dateString?: string) => {
    if (!dateString) return '最近';
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' });
  };

  const formatPrice = (price: number, coinPrice: number | undefined, isFree: boolean) => {
    if (isFree) return '免费';
    if ((coinPrice ?? 0) === 0 && price === 0) return '免费';
    return `${coinPrice ?? 0} 书币`;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      whileHover={{ y: -8 }}
      onHoverStart={() => onHover?.(resource.id)}
      className="group"
    >
      <Link
        href={`/resources/${resource.slug}`}
        aria-label={`查看资源: ${resource.title}`}
        className="
          block bg-white rounded-xl overflow-hidden
          shadow-md hover:shadow-2xl
          transition-all duration-300 ease-smooth
          border border-gray-100
          h-full
          focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2
        "
      >
        {/* 缩略图 */}
        <div className="relative aspect-[4/3] bg-gradient-to-br from-gray-100 to-gray-200 overflow-hidden">
          <ResourceCover
            src={resource.cover_image_url}
            alt={`${resource.title}的缩略图`}
            className="h-full w-full object-cover transition-transform duration-500 ease-smooth group-hover:scale-110"
          />

          {/* 收藏按钮 */}
          <button
            onClick={(e) => {
              e.preventDefault();
              setIsLiked(!isLiked);
            }}
            aria-label={isLiked ? '取消收藏' : '收藏资源'}
            className="
              absolute top-3 right-3 p-2 bg-white/90 backdrop-blur-sm
              rounded-full shadow-lg
              opacity-0 group-hover:opacity-100
              transition-opacity duration-200
              hover:scale-110 transform
              focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-indigo-500
            "
          >
            {isLiked ? (
              <HeartSolidIcon className="w-5 h-5 text-red-500" />
            ) : (
              <HeartIcon className="w-5 h-5 text-gray-600" />
            )}
          </button>

          {/* 价格标签 */}
          <div className="absolute bottom-3 left-3">
            <span
              className={`
                px-3 py-1 rounded-full text-sm font-bold
                backdrop-blur-sm shadow-lg
                ${resource.is_free || (resource.coin_price ?? resource.price) === 0
                  ? 'bg-green-500/90 text-white'
                  : 'bg-gradient-to-r from-orange-500 to-red-500 text-white'
                }
              `}
            >
              {formatPrice(resource.price, resource.coin_price, resource.is_free)}
            </span>
          </div>
        </div>

        {/* 卡片内容 */}
        <div className="p-4">
          {/* 分类标签 */}
          <div className="flex items-center gap-2 mb-3">
            <span className="
              inline-block px-2.5 py-1 
              bg-gradient-to-r from-indigo-50 to-purple-50
              text-indigo-600 text-xs font-semibold rounded-md
            ">
              {resource.resource_type}
            </span>
          </div>

          {/* 标题 */}
          <h3 className="
            text-base font-semibold text-gray-800 mb-2
            line-clamp-2 leading-snug
            group-hover:text-indigo-600
            transition-colors duration-200
            min-h-[3rem]
          ">
            {resource.title}
          </h3>

          {/* 描述（可选） */}
          {resource.description && (
            <p className="text-sm text-gray-600 line-clamp-2 mb-3 leading-relaxed">
              {resource.description}
            </p>
          )}

          {/* 元信息 */}
          <div className="flex items-center justify-between text-xs text-gray-500 pt-3 border-t border-gray-100">
            <div className="flex items-center gap-1">
              <CalendarIcon className="w-4 h-4" />
              <span>{formatDate(resource.created_at)}</span>
            </div>
            <div className="flex items-center gap-1">
              <HeartIcon className="w-4 h-4" />
              <span>{resource.likes_count ?? resource.view_count ?? 0}赞</span>
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}

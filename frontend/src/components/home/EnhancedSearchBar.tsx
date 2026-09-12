'use client';

import { useState, FormEvent } from 'react';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { 
  BookOpenIcon, 
  AcademicCapIcon, 
  DocumentTextIcon,
  SparklesIcon 
} from '@heroicons/react/24/solid';

interface Category {
  value: string;
  label: string;
  icon?: React.ReactNode;
}

interface EnhancedSearchBarProps {
  placeholder?: string;
  onSubmit: (query: string, scope: string) => void;
  categories?: Category[];
}

const defaultCategories: Category[] = [
  { value: 'all', label: '全站', icon: <SparklesIcon className="w-4 h-4" /> },
  { value: 'course', label: '视频课程', icon: <AcademicCapIcon className="w-4 h-4" /> },
  { value: 'ebook', label: '电子书', icon: <BookOpenIcon className="w-4 h-4" /> },
  { value: 'doc', label: '技术文档', icon: <DocumentTextIcon className="w-4 h-4" /> },
];

export default function EnhancedSearchBar({
  placeholder = '搜索优质资源...',
  onSubmit,
  categories = defaultCategories,
}: EnhancedSearchBarProps) {
  const [query, setQuery] = useState('');
  const [scope, setScope] = useState('all');
  const [isFocused, setIsFocused] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      setIsLoading(true);
      try {
        await onSubmit(query, scope);
      } finally {
        setIsLoading(false);
      }
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-3xl mx-auto">
      <div
        className={`
          flex items-stretch bg-white rounded-2xl overflow-hidden
          transition-all duration-250 ease-smooth
          ${isFocused 
            ? 'shadow-2xl ring-4 ring-white/30 scale-[1.02]' 
            : 'shadow-xl hover:shadow-2xl'
          }
        `}
      >
        {/* 分类下拉菜单 */}
        <div className="relative">
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value)}
            className="
              h-full px-4 md:px-6 py-4 bg-gray-50 text-gray-700 font-medium
              border-r border-gray-200 cursor-pointer
              focus:outline-none focus:bg-gray-100
              transition-colors duration-200
              appearance-none pr-10
              text-sm md:text-base
            "
            style={{ minWidth: '120px' }}
          >
            {categories.map((cat) => (
              <option key={cat.value} value={cat.value}>
                {cat.label}
              </option>
            ))}
          </select>
          {/* 下拉箭头 */}
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none">
            <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>

        {/* 搜索输入框 */}
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder}
          className="
            flex-1 px-4 md:px-6 py-4 text-gray-800 placeholder-gray-400
            focus:outline-none
            text-sm md:text-base
            min-w-0
          "
        />

        {/* 搜索按钮 */}
        <button
          type="submit"
          aria-label="搜索"
          disabled={isLoading || !query.trim()}
          className="
            px-6 md:px-8 bg-gradient-to-r from-indigo-600 to-purple-600
            hover:from-indigo-700 hover:to-purple-700
            disabled:from-gray-400 disabled:to-gray-400
            text-white font-semibold
            transition-all duration-200
            flex items-center justify-center gap-2
            disabled:cursor-not-allowed
            min-w-[100px] md:min-w-[120px]
          "
        >
          {isLoading ? (
            <>
              <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span className="hidden md:inline">搜索中</span>
            </>
          ) : (
            <>
              <MagnifyingGlassIcon className="w-5 h-5" />
              <span className="hidden md:inline">搜索</span>
            </>
          )}
        </button>
      </div>

      {/* 热门搜索提示（可选） */}
      <div className="mt-4 text-center">
        <p className="text-sm text-white/70 mb-2">热门搜索：</p>
        <div className="flex flex-wrap justify-center gap-2">
          {['Python', 'JavaScript', 'React', 'AI', '数据结构'].map((tag) => (
            <button
              key={tag}
              type="button"
              onClick={() => {
                setQuery(tag);
                onSubmit(tag, scope);
              }}
              className="
                px-3 py-1 bg-white/20 hover:bg-white/30
                text-white text-sm rounded-full
                transition-colors duration-200
                backdrop-blur-sm
              "
            >
              {tag}
            </button>
          ))}
        </div>
      </div>
    </form>
  );
}

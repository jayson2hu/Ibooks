'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { ReactNode } from 'react';

interface CategoryTab {
  id: string;
  label: string;
  icon?: ReactNode;
  color?: string;
}

interface CategoryTabsProps {
  tabs: CategoryTab[];
  activeTab: string;
  onChange: (tabId: string) => void;
}

export default function CategoryTabs({ tabs, activeTab, onChange }: CategoryTabsProps) {
  return (
    <div className="relative">
      {/* 桌面端标签 */}
      <div className="hidden md:flex items-center gap-2 flex-wrap">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className={`
              relative px-4 py-2 rounded-lg font-medium text-sm
              transition-all duration-200 ease-smooth
              ${activeTab === tab.id
                ? 'text-white shadow-lg'
                : 'text-gray-600 bg-white hover:bg-gray-50 shadow-sm'
              }
            `}
          >
            {/* 活动标签背景 */}
            {activeTab === tab.id && (
              <motion.div
                layoutId="activeTab"
                className="absolute inset-0 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-lg"
                transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
              />
            )}

            {/* 标签内容 */}
            <span className="relative z-10 flex items-center gap-2">
              {tab.icon}
              {tab.label}
            </span>
          </button>
        ))}
      </div>

      {/* 移动端标签 - 水平滚动 */}
      <div className="md:hidden overflow-x-auto scrollbar-hide -mx-4 px-4">
        <div className="flex items-center gap-2 min-w-max pb-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => onChange(tab.id)}
              className={`
                relative px-4 py-2 rounded-lg font-medium text-sm whitespace-nowrap
                transition-all duration-200 ease-smooth
                ${activeTab === tab.id
                  ? 'text-white shadow-lg'
                  : 'text-gray-600 bg-white hover:bg-gray-50 shadow-sm'
                }
              `}
            >
              {activeTab === tab.id && (
                <motion.div
                  layoutId="activeTabMobile"
                  className="absolute inset-0 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-lg"
                  transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
                />
              )}
              <span className="relative z-10 flex items-center gap-2">
                {tab.icon}
                {tab.label}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

'use client';

import { motion } from 'framer-motion';
import { ReactNode, useEffect, useRef, useState } from 'react';

interface FeatureCardProps {
  icon: ReactNode;
  title: string;
  description: string;
  delay?: number;
}

export default function FeatureCard({ icon, title, description, delay = 0 }: FeatureCardProps) {
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.1 }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30 }}
      animate={isVisible ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
      transition={{ duration: 0.6, delay, ease: 'easeOut' }}
      whileHover={{ scale: 1.05, y: -5 }}
      className="
        group p-8 bg-white rounded-2xl shadow-lg hover:shadow-2xl
        transition-all duration-300 ease-smooth
        border border-gray-100
        text-center
      "
    >
      {/* 图标容器 */}
      <div className="
        inline-flex items-center justify-center
        w-16 h-16 mb-6
        bg-gradient-to-br from-indigo-100 to-purple-100
        rounded-2xl
        group-hover:scale-110 group-hover:rotate-6
        transition-all duration-300
      ">
        <div className="text-indigo-600 w-8 h-8">
          {icon}
        </div>
      </div>

      {/* 标题 */}
      <h3 className="text-xl font-bold text-gray-800 mb-3 group-hover:text-indigo-600 transition-colors duration-200">
        {title}
      </h3>

      {/* 描述 */}
      <p className="text-gray-600 leading-relaxed">
        {description}
      </p>
    </motion.div>
  );
}

// 特色功能区组件
interface FeaturesSectionProps {
  features: Array<{
    icon: ReactNode;
    title: string;
    description: string;
  }>;
}

export function FeaturesSection({ features }: FeaturesSectionProps) {
  return (
    <section className="py-20 bg-gradient-to-b from-white to-gray-50">
      <div className="container mx-auto px-4">
        {/* 区块标题 */}
        <div className="text-center mb-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="inline-flex items-center gap-3 mb-4"
          >
            <div className="w-1 h-8 bg-gradient-to-b from-indigo-600 to-purple-600 rounded-full" />
            <h2 className="text-3xl md:text-4xl font-bold text-gray-800">
              为什么选择我们
            </h2>
            <div className="w-1 h-8 bg-gradient-to-b from-indigo-600 to-purple-600 rounded-full" />
          </motion.div>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-gray-600 text-lg max-w-2xl mx-auto"
          >
            我们致力于提供最优质的学习资源和最佳的用户体验
          </motion.p>
        </div>

        {/* 特色卡片网格 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {features.map((feature, index) => (
            <FeatureCard
              key={index}
              icon={feature.icon}
              title={feature.title}
              description={feature.description}
              delay={index * 0.1}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

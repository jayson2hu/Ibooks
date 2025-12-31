'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';

export default function Header() {
    const [isScrolledState, setIsScrolled] = useState(false);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const router = useRouter();
    const pathname = usePathname();
    // Force scrolled style on non-home pages to ensure visibility on white backgrounds
    const isScrolled = isScrolledState || pathname !== '/';

    useEffect(() => {
        const handleScroll = () => {
            setIsScrolled(window.scrollY > 10);
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        if (searchQuery.trim()) {
            router.push(`/search?q=${encodeURIComponent(searchQuery)}`);
            setIsMobileMenuOpen(false);
        }
    };

    return (
        <header
            className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${isScrolled
                ? 'bg-white/80 backdrop-blur-md shadow-sm border-b border-gray-100'
                : 'bg-transparent'
                }`}
        >
            <div className="container mx-auto px-4">
                <div className="flex items-center justify-between h-20">
                    {/* Logo */}
                    <Link href="/" className="flex items-center gap-2 group">
                        <span className="text-3xl transform group-hover:scale-110 transition-transform duration-200">📚</span>
                        <div className={`text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 ${!isScrolled && 'text-white'
                            }`}>
                            资源市场
                        </div>
                    </Link>

                    {/* Desktop Search Bar */}
                    <div className="hidden md:flex flex-1 max-w-xl mx-8">
                        <form onSubmit={handleSearch} className="w-full relative group">
                            <input
                                type="text"
                                placeholder="搜索优质资源..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className={`w-full px-6 py-2.5 rounded-full border transition-all duration-300 outline-none ${isScrolled
                                    ? 'bg-gray-50 border-gray-200 focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-100 text-gray-800'
                                    : 'bg-white/10 border-white/20 text-white placeholder-white/70 focus:bg-white/20 focus:border-white/40'
                                    }`}
                            />
                            <button
                                type="submit"
                                className={`absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-full transition-colors ${isScrolled
                                    ? 'text-gray-400 hover:text-blue-600'
                                    : 'text-white/70 hover:text-white'
                                    }`}
                            >
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                            </button>
                        </form>
                    </div>

                    {/* Desktop Navigation */}
                    <nav className="hidden md:flex items-center gap-8">
                        {[
                            { name: '浏览资源', path: '/resources' },
                            { name: '分类', path: '/categories' },
                            { name: '联系我们', path: '/contact' },
                        ].map((item) => (
                            <Link
                                key={item.path}
                                href={item.path}
                                className={`font-medium text-sm tracking-wide transition-colors relative group ${isScrolled ? 'text-gray-600 hover:text-blue-600' : 'text-white/90 hover:text-white'
                                    }`}
                            >
                                {item.name}
                                <span className={`absolute -bottom-1 left-0 w-0 h-0.5 transition-all duration-300 group-hover:w-full ${isScrolled ? 'bg-blue-600' : 'bg-white'
                                    }`}></span>
                            </Link>
                        ))}
                    </nav>

                    {/* Mobile Menu Button */}
                    <button
                        className="md:hidden p-2 rounded-lg hover:bg-black/5 transition-colors"
                        onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                        aria-label="Toggle menu"
                    >
                        <svg className={`w-6 h-6 ${isScrolled ? 'text-gray-700' : 'text-white'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            {isMobileMenuOpen ? (
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            ) : (
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                            )}
                        </svg>
                    </button>
                </div>

                {/* Mobile Menu */}
                <div className={`md:hidden transition-all duration-300 ease-in-out overflow-hidden ${isMobileMenuOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
                    }`}>
                    <div className="py-4 bg-white rounded-xl shadow-xl mt-2 border border-gray-100">
                        <div className="px-4 mb-4">
                            <form onSubmit={handleSearch} className="relative">
                                <input
                                    type="text"
                                    placeholder="搜索..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                                />
                                <button type="submit" className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                    </svg>
                                </button>
                            </form>
                        </div>
                        {[
                            { name: '浏览资源', path: '/resources' },
                            { name: '分类', path: '/categories' },
                            { name: '联系我们', path: '/contact' },
                        ].map((item) => (
                            <Link
                                key={item.path}
                                href={item.path}
                                className="block px-4 py-3 text-gray-600 hover:bg-blue-50 hover:text-blue-600 transition-colors font-medium"
                                onClick={() => setIsMobileMenuOpen(false)}
                            >
                                {item.name}
                            </Link>
                        ))}
                    </div>
                </div>
            </div>
        </header>
    );
}

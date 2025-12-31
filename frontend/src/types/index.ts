/**
 * TypeScript types and interfaces
 */

export interface User {
    id: number;
    email: string;
    username: string;
    full_name?: string;
    role: 'admin' | 'user' | 'moderator';
    status: 'active' | 'inactive' | 'suspended';
    avatar_url?: string;
    created_at: string;
    last_login_at?: string;
}

export interface Resource {
    id: number;
    title: string;
    slug: string;
    description?: string;
    excerpt?: string;
    category_id?: number;
    tags: string[];
    price: number;
    original_price?: number;
    is_free: boolean;
    file_size?: string;
    file_format?: string;
    resource_type?: string;
    cover_image_url?: string;
    is_published: boolean;
    is_featured: boolean;
    view_count: number;
    download_count: number;
    created_at: string;
    updated_at: string;
    published_at?: string;
}

export interface ResourceDetail extends Resource {
    cloud_link?: string;
    access_code?: string;
    backup_links: string[];
    preview_images: string[];
}

export interface Category {
    id: number;
    name: string;
    slug: string;
    description?: string;
    parent_id?: number;
    icon?: string;
    color?: string;
    cover_image_url?: string;
    is_active: boolean;
    sort_order: number;
    resource_count: number;
    created_at: string;
}

export interface CategoryTree extends Category {
    children: CategoryTree[];
}

export interface Contact {
    id: number;
    type: 'wechat' | 'wechat_qr' | 'qq' | 'qq_group' | 'email' | 'phone' | 'telegram' | 'whatsapp' | 'other';
    label: string;
    value: string;
    qr_code_url?: string;
    icon?: string;
    color?: string;
    description?: string;
    is_copyable: boolean;
    is_clickable: boolean;
    link_url?: string;
    is_active: boolean;
    display_order: number;
    show_in_header: boolean;
    show_in_footer: boolean;
    show_in_contact_page: boolean;
    show_in_sidebar: boolean;
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    page_size: number;
    pages: number;
}

export interface ApiError {
    detail: string;
    code?: string;
}

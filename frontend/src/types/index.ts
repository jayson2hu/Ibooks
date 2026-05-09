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
    coin_price: number;
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

export interface ResourceAccess {
    cloud_link?: string | null;
    backup_links: string[];
    access_code?: string | null;
}

export type OrderStatus = 'pending' | 'paid' | 'cancelled' | 'refunded';
export type PaymentMethod = 'alipay' | 'wechat' | 'free' | 'coin';

export interface Order {
    id: number;
    order_no: string;
    user_id: number;
    resource_id: number;
    amount: number | string;
    coin_amount: number;
    payment_method?: PaymentMethod | null;
    status: OrderStatus;
    trade_no?: string | null;
    paid_at?: string | null;
    created_at: string;
    updated_at: string;
    resource?: Resource | null;
    user?: User | null;
}

export interface AlipayCreateResponse {
    payment_url: string;
    order_no?: string;
    recharge_no?: string;
}

export interface Wallet {
    id: number;
    user_id: number;
    balance: number;
    total_recharged: number;
    total_spent: number;
    total_rewarded: number;
    created_at: string;
    updated_at: string;
}

export interface AdminWallet extends Wallet {
    user?: User | null;
}

export type CoinLedgerType = 'recharge' | 'purchase' | 'refund' | 'signin' | 'admin_adjust';

export interface CoinLedger {
    id: number;
    user_id: number;
    wallet_id: number;
    amount: number;
    balance_after: number;
    type: CoinLedgerType;
    related_order_no?: string | null;
    description?: string | null;
    created_at: string;
}

export interface AdminCoinLedger extends CoinLedger {
    user?: User | null;
}

export interface SigninStatus {
    enabled: boolean;
    reward_coins: number;
    signed_in_today: boolean;
    signin_date: string;
}

export interface SigninResult {
    id: number;
    user_id: number;
    signin_date: string;
    reward_coins: number;
    created_at: string;
    balance: number;
}

export interface RechargePackage {
    id: number;
    name: string;
    coins: number;
    bonus_coins: number;
    amount: number | string;
    is_active: boolean;
    sort_order: number;
    created_at: string;
    updated_at: string;
}

export type RechargeOrderStatus = 'pending' | 'paid' | 'cancelled' | 'failed';
export type RechargePaymentMethod = 'alipay' | 'wechat';

export interface RechargeOrder {
    id: number;
    recharge_no: string;
    user_id: number;
    package_id?: number | null;
    coins: number;
    bonus_coins: number;
    amount: number | string;
    payment_method: RechargePaymentMethod;
    status: RechargeOrderStatus;
    trade_no?: string | null;
    paid_at?: string | null;
    created_at: string;
    updated_at: string;
    package?: RechargePackage | null;
    user?: User | null;
}

export interface SigninSettings {
    enabled: boolean;
    reward_coins: number;
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

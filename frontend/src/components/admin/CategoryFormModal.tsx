'use client';

import { useCallback, useEffect, useId, useMemo, useRef, useState } from 'react';
import type { FormEvent, MouseEvent } from 'react';
import { api, getApiErrorMessage } from '@/lib/api';
import type { Category, CategoryCreateInput, CategoryUpdateInput } from '@/types';

interface CategoryFormModalProps {
    categories: Category[];
    category?: Category | null;
    onClose: () => void;
    onSaved: (action: 'created' | 'updated' | 'created-partial') => Promise<void>;
}

interface CategoryFormState {
    name: string;
    description: string;
    parentId: string;
    sortOrder: string;
    isActive: boolean;
}

interface CategoryFieldErrors {
    name?: string;
    parentId?: string;
    sortOrder?: string;
}

function buildInitialState(category?: Category | null): CategoryFormState {
    return {
        name: category?.name ?? '',
        description: category?.description ?? '',
        parentId: category?.parent_id ? String(category.parent_id) : '',
        sortOrder: String(category?.sort_order ?? 0),
        isActive: category?.is_active ?? true,
    };
}

function getUnavailableParentIds(categories: Category[], currentCategoryId?: number): Set<number> {
    const unavailable = new Set<number>();
    if (!currentCategoryId) {
        return unavailable;
    }

    const pending = [currentCategoryId];
    while (pending.length > 0) {
        const parentId = pending.shift();
        if (!parentId || unavailable.has(parentId)) {
            continue;
        }

        unavailable.add(parentId);
        categories.forEach((category) => {
            if (category.parent_id === parentId && !unavailable.has(category.id)) {
                pending.push(category.id);
            }
        });
    }

    return unavailable;
}

export default function CategoryFormModal({
    categories,
    category,
    onClose,
    onSaved,
}: CategoryFormModalProps) {
    const [form, setForm] = useState<CategoryFormState>(() => buildInitialState(category));
    const [fieldErrors, setFieldErrors] = useState<CategoryFieldErrors>({});
    const [submitError, setSubmitError] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [generatedSlug, setGeneratedSlug] = useState(category?.slug ?? '');
    const dialogRef = useRef<HTMLDivElement>(null);
    const nameInputRef = useRef<HTMLInputElement>(null);
    const isSubmittingRef = useRef(false);
    const persistedCategoryIdRef = useRef<number | null>(null);
    const titleId = useId();
    const slugDescriptionId = useId();

    const unavailableParentIds = useMemo(
        () => getUnavailableParentIds(categories, category?.id),
        [categories, category?.id],
    );
    const parentOptions = useMemo(
        () => categories.filter((item) => !unavailableParentIds.has(item.id)),
        [categories, unavailableParentIds],
    );

    useEffect(() => {
        isSubmittingRef.current = isSubmitting;
    }, [isSubmitting]);

    const requestClose = useCallback(() => {
        if (isSubmittingRef.current) {
            return;
        }

        if (!category && persistedCategoryIdRef.current) {
            void onSaved('created-partial');
            return;
        }

        onClose();
    }, [category, onClose, onSaved]);

    useEffect(() => {
        const previouslyFocused = document.activeElement instanceof HTMLElement
            ? document.activeElement
            : null;
        nameInputRef.current?.focus();

        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === 'Escape' && !isSubmittingRef.current) {
                event.preventDefault();
                requestClose();
                return;
            }

            if (event.key !== 'Tab' || !dialogRef.current) {
                return;
            }

            const focusableElements = Array.from(
                dialogRef.current.querySelectorAll<HTMLElement>(
                    'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
                ),
            ).filter((element) => element.getAttribute('aria-hidden') !== 'true');

            if (focusableElements.length === 0) {
                return;
            }

            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];
            if (event.shiftKey && document.activeElement === firstElement) {
                event.preventDefault();
                lastElement.focus();
            } else if (!event.shiftKey && document.activeElement === lastElement) {
                event.preventDefault();
                firstElement.focus();
            }
        };

        document.addEventListener('keydown', handleKeyDown);
        return () => {
            document.removeEventListener('keydown', handleKeyDown);
            previouslyFocused?.focus();
        };
    }, [requestClose]);

    const updateField = <Key extends keyof CategoryFormState,>(
        field: Key,
        value: CategoryFormState[Key],
    ) => {
        setForm((current) => ({ ...current, [field]: value }));
        setFieldErrors({});
        setSubmitError('');
    };

    const validate = (): { parentId: number | null; sortOrder: number } | null => {
        const errors: CategoryFieldErrors = {};
        const trimmedName = form.name.trim();
        const parsedSortOrder = Number(form.sortOrder);
        const parsedParentId = form.parentId ? Number(form.parentId) : null;

        if (!trimmedName) {
            errors.name = '请输入分类名称';
        } else if (trimmedName.length > 200) {
            errors.name = '分类名称不能超过 200 个字符';
        }

        if (!form.sortOrder.trim() || !Number.isInteger(parsedSortOrder)) {
            errors.sortOrder = '排序值必须是整数';
        }

        if (
            parsedParentId !== null
            && (!Number.isInteger(parsedParentId) || !parentOptions.some((item) => item.id === parsedParentId))
        ) {
            errors.parentId = '请选择有效的父分类';
        }

        setFieldErrors(errors);
        if (Object.keys(errors).length > 0) {
            return null;
        }

        return { parentId: parsedParentId, sortOrder: parsedSortOrder };
    };

    const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (isSubmittingRef.current) {
            return;
        }

        setSubmitError('');
        const validated = validate();
        if (!validated) {
            return;
        }

        const description = form.description.trim() || null;
        const createPayload: CategoryCreateInput = {
            name: form.name.trim(),
            description,
            parent_id: validated.parentId,
        };
        const updatePayload: CategoryUpdateInput = {
            ...createPayload,
            sort_order: validated.sortOrder,
            is_active: form.isActive,
        };

        isSubmittingRef.current = true;
        setIsSubmitting(true);
        try {
            const existingId = category?.id ?? persistedCategoryIdRef.current;
            if (existingId) {
                const response = await api.categories.update(existingId, updatePayload);
                setGeneratedSlug(response.data.slug);
            } else {
                const response = await api.categories.create(createPayload);
                const createdCategory = response.data;
                persistedCategoryIdRef.current = createdCategory.id;
                setGeneratedSlug(createdCategory.slug);

                if (
                    createdCategory.sort_order !== validated.sortOrder
                    || createdCategory.is_active !== form.isActive
                ) {
                    await api.categories.update(createdCategory.id, {
                        sort_order: validated.sortOrder,
                        is_active: form.isActive,
                    });
                }
            }

            await onSaved(category ? 'updated' : 'created');
        } catch (error: unknown) {
            const message = getApiErrorMessage(error, category ? '分类更新失败' : '分类创建失败');
            if (!category && persistedCategoryIdRef.current) {
                setSubmitError(`分类已创建，但排序或启用状态保存失败：${message}。请重试。`);
            } else {
                setSubmitError(message);
            }
        } finally {
            isSubmittingRef.current = false;
            setIsSubmitting(false);
        }
    };

    const handleBackdropMouseDown = (event: MouseEvent<HTMLDivElement>) => {
        if (event.target === event.currentTarget && !isSubmitting) {
            requestClose();
        }
    };

    const isEditing = Boolean(category || persistedCategoryIdRef.current);

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
            onMouseDown={handleBackdropMouseDown}
        >
            <div
                ref={dialogRef}
                role="dialog"
                aria-modal="true"
                aria-labelledby={titleId}
                aria-busy={isSubmitting}
                className="max-h-[calc(100vh-2rem)] w-full max-w-lg overflow-y-auto rounded-xl bg-white shadow-xl"
            >
                <div className="flex items-start justify-between border-b border-gray-200 px-6 py-5">
                    <div>
                        <h2 id={titleId} className="text-xl font-bold text-gray-900">
                            {isEditing ? '编辑分类' : '创建分类'}
                        </h2>
                        <p className="mt-1 text-sm text-gray-500">
                            填写分类信息，带 * 的字段为必填项。
                        </p>
                    </div>
                    <button
                        type="button"
                        onClick={requestClose}
                        disabled={isSubmitting}
                        aria-label="关闭分类表单"
                        className="rounded-lg p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                        <span aria-hidden="true" className="text-xl leading-none">×</span>
                    </button>
                </div>

                <form onSubmit={handleSubmit} noValidate className="space-y-5 px-6 py-5">
                    {submitError && (
                        <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                            {submitError}
                        </div>
                    )}

                    <div>
                        <label htmlFor="category-name" className="mb-1.5 block text-sm font-medium text-gray-700">
                            分类名称 <span aria-hidden="true" className="text-red-500">*</span>
                        </label>
                        <input
                            ref={nameInputRef}
                            id="category-name"
                            type="text"
                            value={form.name}
                            onChange={(event) => updateField('name', event.target.value)}
                            maxLength={200}
                            required
                            disabled={isSubmitting}
                            aria-invalid={Boolean(fieldErrors.name)}
                            aria-describedby={fieldErrors.name ? 'category-name-error' : undefined}
                            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                            placeholder="例如：编程开发"
                        />
                        {fieldErrors.name && (
                            <p id="category-name-error" className="mt-1.5 text-sm text-red-600">
                                {fieldErrors.name}
                            </p>
                        )}
                    </div>

                    <div>
                        <label htmlFor="category-slug" className="mb-1.5 block text-sm font-medium text-gray-700">
                            Slug（自动生成）
                        </label>
                        <input
                            id="category-slug"
                            type="text"
                            value={generatedSlug}
                            readOnly
                            disabled={isSubmitting}
                            aria-describedby={slugDescriptionId}
                            className="w-full cursor-not-allowed rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-gray-600"
                            placeholder="保存后由服务端生成"
                        />
                        <p id={slugDescriptionId} className="mt-1.5 text-xs text-gray-500">
                            后端会根据名称生成 Slug；修改名称后 Slug 会在保存时同步更新。
                        </p>
                    </div>

                    <div>
                        <label htmlFor="category-description" className="mb-1.5 block text-sm font-medium text-gray-700">
                            描述
                        </label>
                        <textarea
                            id="category-description"
                            value={form.description}
                            onChange={(event) => updateField('description', event.target.value)}
                            rows={4}
                            disabled={isSubmitting}
                            className="w-full resize-y rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                            placeholder="简要说明该分类包含的内容"
                        />
                    </div>

                    <div>
                        <label htmlFor="category-parent" className="mb-1.5 block text-sm font-medium text-gray-700">
                            父分类
                        </label>
                        <select
                            id="category-parent"
                            value={form.parentId}
                            onChange={(event) => updateField('parentId', event.target.value)}
                            disabled={isSubmitting}
                            aria-invalid={Boolean(fieldErrors.parentId)}
                            aria-describedby={fieldErrors.parentId ? 'category-parent-error' : undefined}
                            className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                        >
                            <option value="">无（顶级分类）</option>
                            {parentOptions.map((item) => (
                                <option key={item.id} value={item.id}>
                                    {item.name}（{item.slug}）
                                </option>
                            ))}
                        </select>
                        {fieldErrors.parentId && (
                            <p id="category-parent-error" className="mt-1.5 text-sm text-red-600">
                                {fieldErrors.parentId}
                            </p>
                        )}
                    </div>

                    <div className="grid gap-5 sm:grid-cols-2">
                        <div>
                            <label htmlFor="category-sort-order" className="mb-1.5 block text-sm font-medium text-gray-700">
                                排序值 <span aria-hidden="true" className="text-red-500">*</span>
                            </label>
                            <input
                                id="category-sort-order"
                                type="number"
                                step="1"
                                value={form.sortOrder}
                                onChange={(event) => updateField('sortOrder', event.target.value)}
                                required
                                disabled={isSubmitting}
                                aria-invalid={Boolean(fieldErrors.sortOrder)}
                                aria-describedby={fieldErrors.sortOrder ? 'category-sort-error' : 'category-sort-help'}
                                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                            />
                            {fieldErrors.sortOrder ? (
                                <p id="category-sort-error" className="mt-1.5 text-sm text-red-600">
                                    {fieldErrors.sortOrder}
                                </p>
                            ) : (
                                <p id="category-sort-help" className="mt-1.5 text-xs text-gray-500">
                                    数值越小越靠前。
                                </p>
                            )}
                        </div>

                        <div className="flex items-center pt-7">
                            <label className="flex cursor-pointer items-center gap-3 text-sm font-medium text-gray-700">
                                <input
                                    type="checkbox"
                                    checked={form.isActive}
                                    onChange={(event) => updateField('isActive', event.target.checked)}
                                    disabled={isSubmitting}
                                    className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                />
                                启用分类
                            </label>
                        </div>
                    </div>

                    <div className="flex flex-col-reverse gap-3 border-t border-gray-200 pt-5 sm:flex-row sm:justify-end">
                        <button
                            type="button"
                            onClick={requestClose}
                            disabled={isSubmitting}
                            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            取消
                        </button>
                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                            {isSubmitting ? '保存中...' : '保存分类'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

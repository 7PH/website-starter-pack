// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

export interface ModalOptions {
    /** Z-index for stacking modals */
    zIndex?: number;
    /** Additional CSS classes */
    classes?: string;
    /** Allow any additional options */
    [key: string]: unknown;
}

export interface ModalRecord {
    /** Whether the modal is currently open */
    open: boolean;
    /** Options passed when opening the modal */
    options: ModalOptions;
    /** Internal promise for async resolution */
    _resolve?: (value: unknown) => void;
}

export interface ConfirmModalOptions extends ModalOptions {
    /** Modal title */
    title?: string;
    /** Modal message/description */
    message?: string;
    /** Confirm button text */
    confirmText?: string;
    /** Cancel button text */
    cancelText?: string;
    /** Confirm button color (danger, primary, etc.) */
    confirmColor?: 'primary' | 'error' | 'warning' | 'success' | 'neutral';
}

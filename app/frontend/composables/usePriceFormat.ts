// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import { formatInterval, formatPrice } from '~/utils/formatters';

/**
 * Price and billing-interval formatters bound to the current UI locale ("8,00 € / mois" in French).
 */
export function usePriceFormat() {
    const { t, te, locale } = useI18n();
    return {
        formatPrice: (amount: number, currency: string) => formatPrice(amount, currency, locale.value),
        formatInterval: (interval: string) => {
            const key = `core.billing.interval.${interval}`;
            return te(key) ? t(key) : formatInterval(interval);
        },
    };
}

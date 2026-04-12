// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import { readdirSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const LOCALES_DIR = resolve(__dirname, '../locales');

function deepMerge(target: Record<string, unknown>, source: Record<string, unknown>): Record<string, unknown> {
    const result = { ...target };
    for (const key of Object.keys(source)) {
        const t = result[key];
        const s = source[key];
        if (t && s && typeof t === 'object' && typeof s === 'object' && !Array.isArray(t) && !Array.isArray(s)) {
            result[key] = deepMerge(t as Record<string, unknown>, s as Record<string, unknown>);
        } else {
            result[key] = s;
        }
    }
    return result;
}

function getKeys(obj: Record<string, unknown>, prefix = ''): Set<string> {
    const keys = new Set<string>();
    for (const key of Object.keys(obj)) {
        const path = prefix ? `${prefix}.${key}` : key;
        const value = obj[key];
        if (value && typeof value === 'object' && !Array.isArray(value)) {
            for (const nested of getKeys(value as Record<string, unknown>, path)) {
                keys.add(nested);
            }
        } else {
            keys.add(path);
        }
    }
    return keys;
}

function discoverLocales(): Map<string, Record<string, unknown>> {
    const files = readdirSync(LOCALES_DIR).filter((f) => f.endsWith('.json'));
    const langs = new Set<string>();

    for (const file of files) {
        const match = file.match(/^(?:core-)?(.+)\.json$/);
        if (match?.[1]) langs.add(match[1]);
    }

    const merged = new Map<string, Record<string, unknown>>();
    for (const lang of langs) {
        const load = (name: string) => {
            try {
                return JSON.parse(readFileSync(resolve(LOCALES_DIR, name), 'utf-8'));
            } catch {
                return {};
            }
        };
        merged.set(lang, deepMerge(load(`core-${lang}.json`), load(`${lang}.json`)));
    }

    return merged;
}

describe('i18n alignment', () => {
    const locales = discoverLocales();
    const langs = [...locales.keys()].sort();
    const allKeys = new Map<string, Set<string>>();

    for (const lang of langs) {
        allKeys.set(lang, getKeys(locales.get(lang)!));
    }

    const union = new Set<string>();
    for (const keys of allKeys.values()) {
        for (const k of keys) union.add(k);
    }

    it(`should have at least 2 locales`, () => {
        expect(langs.length).toBeGreaterThanOrEqual(2);
    });

    for (const lang of langs) {
        it(`"${lang}" should have all translation keys`, () => {
            const keys = allKeys.get(lang)!;
            const missing = [...union].filter((k) => !keys.has(k)).sort();
            expect(missing, `Missing keys in "${lang}":\n  ${missing.join('\n  ')}`).toEqual([]);
        });
    }
});

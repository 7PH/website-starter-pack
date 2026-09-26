// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import { describe, expect, it } from 'vitest';
import { detectLastNameFirst, splitNameLine } from '~/utils/name-import';

describe('detectLastNameFirst', () => {
    it('detects ALL-CAPS surnames written first', () => {
        expect(detectLastNameFirst(['MARTIN Alice', 'DUPONT Léa', 'Paul Durand'], ' ')).toBe(true);
    });

    it('keeps the default order for "First LAST" and plain names', () => {
        expect(detectLastNameFirst(['Alice MARTIN', 'Léa DUPONT'], ' ')).toBe(false);
        expect(detectLastNameFirst(['Alice Martin', 'Léa Dupont'], ' ')).toBe(false);
    });

    it('ignores initials, all-caps lines and single names', () => {
        expect(detectLastNameFirst(['A Martin', 'ALICE MARTIN', 'Alice'], ' ')).toBe(false);
    });

    it('works with other delimiters', () => {
        expect(detectLastNameFirst(['ÉLOI;Jean', 'MARTIN;Alice'], ';')).toBe(true);
    });
});

describe('splitNameLine', () => {
    it('splits on runs of spaces or on the delimiter', () => {
        expect(splitNameLine('  MARTIN   Alice ', ' ')).toEqual(['MARTIN', 'Alice']);
        expect(splitNameLine('Martin, Alice', ',')).toEqual(['Martin', 'Alice']);
    });
});

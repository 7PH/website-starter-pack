// ⚠️ STARTERPACK CORE — DO NOT MODIFY
/**
 * Example unit tests demonstrating Vitest setup.
 *
 * Add your own tests following this pattern:
 * - Create test files in tests/ directory
 * - Name them *.test.ts
 * - Use describe/it/expect from vitest
 */

import { describe, it, expect } from 'vitest';

describe('Example Tests', () => {
    it('should perform basic assertions', () => {
        expect(1 + 1).toBe(2);
        expect('hello').toContain('ell');
        expect([1, 2, 3]).toHaveLength(3);
    });

    it('should handle async operations', async () => {
        const result = await Promise.resolve('async value');
        expect(result).toBe('async value');
    });

    it('should work with objects', () => {
        const user = { name: 'Test', email: 'test@example.com' };
        expect(user).toHaveProperty('name');
        expect(user.email).toMatch(/@/);
    });
});

// Example of testing a utility function
// Uncomment and adapt when you have actual utilities to test:
//
// import { formatDate } from '~/utils/date'
//
// describe('formatDate', () => {
//     it('should format dates correctly', () => {
//         const date = new Date('2024-01-15')
//         expect(formatDate(date)).toBe('January 15, 2024')
//     })
// })

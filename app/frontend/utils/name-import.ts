// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

const isAllCaps = (word: string) => word.length > 1 && word === word.toUpperCase() && word !== word.toLowerCase();

/**
 * Split one pasted name line into its first two fields.
 */
export function splitNameLine(line: string, delimiter: string): [string, string] {
    const parts = delimiter === ' ' ? line.trim().split(/\s+/, 2) : line.split(delimiter, 2);
    return [(parts[0] ?? '').trim(), (parts[1] ?? '').trim()];
}

/**
 * True when most lines read like "MARTIN Alice": an ALL-CAPS first field followed by one that isn't.
 * School exports commonly write the surname first in capitals.
 */
export function detectLastNameFirst(lines: string[], delimiter: string): boolean {
    const pairs = lines.map((line) => splitNameLine(line, delimiter)).filter(([a, b]) => a && b);
    const votes = pairs.filter(([a, b]) => isAllCaps(a) && !isAllCaps(b)).length;
    return pairs.length > 0 && votes > pairs.length / 2;
}

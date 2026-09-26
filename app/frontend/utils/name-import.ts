// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

const isAllCaps = (word: string) => word.length > 1 && word === word.toUpperCase() && word !== word.toLowerCase();

/**
 * Split one pasted name line into two fields. With spaces, the cut falls where an ALL-CAPS run (the
 * surname) meets the rest, so "DE LA TOUR Hugo" and "Jean Pierre MARTIN" stay whole; otherwise after the first word.
 */
export function splitNameLine(line: string, delimiter: string): [string, string] {
    if (delimiter !== ' ') {
        const [first = '', second = ''] = line.split(delimiter, 2);
        return [first.trim(), second.trim()];
    }
    const words = line.trim().split(/\s+/);
    const caps = words.map(isAllCaps);
    const boundary = caps.findIndex((c) => c !== caps[0]);
    const cut = boundary > 0 && caps.slice(boundary).every((c) => c === caps[boundary]) ? boundary : 1;
    return [words.slice(0, cut).join(' '), words.slice(cut).join(' ')];
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

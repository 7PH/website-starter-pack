module.exports = {
    root: true,
    env: {
        browser: true,
        node: true,
        es2021: true,
    },
    extends: [
        'plugin:@typescript-eslint/recommended',
        'plugin:vue/recommended',
        'plugin:nuxt/recommended',
        'plugin:import/recommended',
        'plugin:prettier/recommended',
    ],
    parser: 'vue-eslint-parser',
    parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        parser: '@typescript-eslint/parser',
    },
    settings: {
        'import/extensions': ['.vue', '.ts', '.tsx'],
    },
    plugins: ['vue', '@typescript-eslint'],
    rules: {
        // Let Prettier handle all formatting (indent, quotes, semi, etc.)
        // Only keep non-formatting rules here
        'vue/no-multiple-template-root': 'off',
        'vue/multi-word-component-names': 'off',
        'vue/no-v-model-argument': 'off', // Vue 3 supports v-model arguments
        '@typescript-eslint/no-unused-vars': 'off',
        'import/no-unresolved': 'off', // Nuxt auto-imports and ~/ alias not recognized
    },
};

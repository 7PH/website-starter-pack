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
        indent: ['error', 4],
        'linebreak-style': ['error', 'unix'],
        quotes: ['error', 'single'],
        semi: ['error', 'always'],
        'space-unary-ops': [
            'error',
            {
                words: true,
                nonwords: true,
            },
        ],
        'no-multiple-empty-lines': ['error', { max: 2, maxEOF: 1 }],
        'vue/html-indent': [
            'error',
            4,
        ],
        'vue/no-multiple-template-root': 'off',
        'vue/multi-word-component-names': 'off',
        'vue/multiline-html-element-content-newline': ['error', {
            ignoreWhenEmpty: true,
            allowEmptyLines: false,
        }],
        'arrow-parens': ['error', 'as-needed'],
        'import/newline-after-import': ['warn', { count: 2 }],
        'comma-dangle': ['error', 'always-multiline'],
        'space-before-function-paren': ['error', {
            anonymous: 'always',
            asyncArrow: 'always',
            named: 'never',
        }],
        '@typescript-eslint/no-unused-vars': 'off'
    },
};

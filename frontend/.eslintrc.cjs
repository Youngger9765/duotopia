module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true,
    },
  },
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  rules: {
    // 基本規則
    'no-unused-vars': 'warn',
    'no-undef': 'warn',
  },
}
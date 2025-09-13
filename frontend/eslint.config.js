import js from '@eslint/js';
import typescript from '@typescript-eslint/eslint-plugin';
import typescriptParser from '@typescript-eslint/parser';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import globals from 'globals';

export default [
  js.configs.recommended,
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      parser: typescriptParser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        ecmaFeatures: {
          jsx: true,
        },
        // project: './tsconfig.json',  // 需要完整路徑設定，暫時關閉
        // tsconfigRootDir: import.meta.dirname,
      },
      globals: {
        ...globals.browser,
        ...globals.es2020,
      },
    },
    plugins: {
      '@typescript-eslint': typescript,
      'react': react,
      'react-hooks': reactHooks,
    },
    settings: {
      react: {
        version: 'detect',
      },
    },
    rules: {
      // TypeScript rules - 嚴格型別檢查
      '@typescript-eslint/no-unused-vars': 'warn',
      '@typescript-eslint/no-explicit-any': 'error',  // 禁止使用 any！
      // TODO: 下面這些規則需要 parserOptions.project，暫時關閉
      // '@typescript-eslint/no-unsafe-assignment': 'error',
      // '@typescript-eslint/no-unsafe-member-access': 'error',
      // '@typescript-eslint/no-unsafe-call': 'error',
      '@typescript-eslint/explicit-module-boundary-types': 'off',

      // React rules
      'react/react-in-jsx-scope': 'off',
      'react/prop-types': 'off',

      // General rules
      'no-undef': 'off',
      'no-unused-vars': 'off',
    },
  },
  {
    ignores: ['dist/', 'node_modules/', 'vite.config.ts', '.eslintrc.cjs'],
  },
];

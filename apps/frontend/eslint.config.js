import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'

export default tseslint.config(
  { ignores: ['dist'] },
  {
    // ==================== 推荐配置集（行业标准）====================
    extends: [
      js.configs.recommended,
      ...tseslint.configs.recommendedTypeChecked,  // 推荐的类型检查（从 strict 降级）
      // 移除 stylisticTypeChecked - 减少过度严格的风格检查
    ],
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      // ==================== React Hooks 规则 ====================
      ...reactHooks.configs.recommended.rules,
      'react-hooks/exhaustive-deps': 'error',     // 严格检查 hooks 依赖

      // ==================== React Refresh ====================
      'react-refresh/only-export-components': [
        'error',
        { allowConstantExport: true },
      ],

      // ==================== 代码质量 ====================
      'no-console': ['error', { allow: ['error', 'warn'] }],
      'no-debugger': 'error',
      'no-alert': 'error',
      'no-var': 'error',
      'prefer-const': 'error',
      'prefer-arrow-callback': 'error',
      'prefer-template': 'error',
      'prefer-spread': 'error',
      'prefer-rest-params': 'error',
      'no-implicit-coercion': 'error',
      'no-param-reassign': 'error',
      'no-return-await': 'error',
      'require-await': 'error',
      'no-unused-expressions': 'error',
      'no-nested-ternary': 'warn',
      'max-depth': ['warn', 4],
      'max-lines-per-function': ['warn', { max: 300, skipBlankLines: true, skipComments: true }],
      'complexity': ['warn', 20],

      // ==================== TypeScript 核心规则（保留）====================
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/no-floating-promises': 'error',
      '@typescript-eslint/no-misused-promises': 'error',
      '@typescript-eslint/await-thenable': 'error',

      // ==================== TypeScript Unsafe 规则（降级为 warn）====================
      '@typescript-eslint/no-unsafe-assignment': 'warn',       // error -> warn
      '@typescript-eslint/no-unsafe-call': 'warn',             // error -> warn
      '@typescript-eslint/no-unsafe-member-access': 'warn',    // error -> warn
      '@typescript-eslint/no-unsafe-return': 'warn',           // error -> warn
      '@typescript-eslint/no-unsafe-argument': 'warn',         // error -> warn

      // ==================== TypeScript 风格规则（放宽）====================
      '@typescript-eslint/explicit-function-return-type': 'off',       // error -> off
      '@typescript-eslint/strict-boolean-expressions': 'off',          // error -> off
      '@typescript-eslint/no-unnecessary-condition': 'warn',           // error -> warn
      '@typescript-eslint/no-unnecessary-type-assertion': 'warn',      // error -> warn
      '@typescript-eslint/prefer-nullish-coalescing': 'warn',          // error -> warn
      '@typescript-eslint/prefer-optional-chain': 'warn',              // error -> warn
      '@typescript-eslint/prefer-readonly': 'warn',                    // error -> warn
      '@typescript-eslint/switch-exhaustiveness-check': 'error',

      // ==================== TypeScript 导入导出（保留）====================
      '@typescript-eslint/consistent-type-imports': [
        'warn',  // error -> warn
        { prefer: 'type-imports', fixStyle: 'separate-type-imports' },
      ],
      '@typescript-eslint/consistent-type-exports': [
        'warn',  // error -> warn
        { fixMixedExportsWithInlineTypeSpecifier: true },
      ],
      '@typescript-eslint/no-unused-vars': [
        'error',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
          caughtErrorsIgnorePattern: '^_',
        },
      ],
      '@typescript-eslint/naming-convention': [
        'error',
        {
          selector: 'variable',
          format: ['camelCase', 'PascalCase', 'UPPER_CASE'],
        },
        {
          selector: 'function',
          format: ['camelCase', 'PascalCase'],
        },
        {
          selector: 'typeLike',
          format: ['PascalCase'],
        },
        {
          selector: 'interface',
          format: ['PascalCase'],
          custom: {
            regex: '^I[A-Z]',
            match: false,
          },
        },
      ],

      // ==================== 导入规则 ====================
      'no-duplicate-imports': 'error',
      'sort-imports': [
        'error',
        {
          ignoreCase: true,
          ignoreDeclarationSort: true,
        },
      ],

      // ==================== 临时禁用有 bug 的规则 ====================
      '@typescript-eslint/only-throw-error': 'off',  // ESLint 8.46.3 有 bug
    },
  },
)

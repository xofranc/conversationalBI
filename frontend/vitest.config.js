import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['src/**/*.test.js'],
    coverage: {
      provider: 'v8',
      include: ['src/infrastructure/charts/**/*.js', 'src/domain/charts/**/*.js'],
    },
  },
});

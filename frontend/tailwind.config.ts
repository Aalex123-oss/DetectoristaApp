import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        panel: '#0f1720',
        panelSoft: '#16212c',
        edge: '#243444',
        accent: '#38bdf8',
        warn: '#f59e0b',
        danger: '#ef4444',
        ok: '#22c55e',
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
    },
  },
  plugins: [],
};

export default config;

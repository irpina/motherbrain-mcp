import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "var(--border)",
        "border-subtle": "var(--border-subtle)",
        background: "var(--bg-base)",
        foreground: "var(--text-primary)",
        elevated: "var(--bg-elevated)",
        subtle: "var(--bg-subtle)",
        input: "var(--bg-input)",
        primary: {
          DEFAULT: "var(--accent)",
          hover: "var(--accent-hover)",
          dim: "var(--accent-dim)",
          foreground: "#ffffff",
        },
        muted: {
          DEFAULT: "var(--bg-subtle)",
          foreground: "var(--text-secondary)",
        },
        card: {
          DEFAULT: "var(--bg-elevated)",
          foreground: "var(--text-primary)",
        },
        destructive: {
          DEFAULT: "var(--danger)",
          dim: "var(--danger-dim)",
          foreground: "#ffffff",
        },
        success: {
          DEFAULT: "var(--success)",
          dim: "var(--success-dim)",
          foreground: "#ffffff",
        },
        warning: {
          DEFAULT: "var(--warning)",
          dim: "var(--warning-dim)",
          foreground: "#ffffff",
        },
        accent: {
          DEFAULT: "var(--accent)",
          hover: "var(--accent-hover)",
          dim: "var(--accent-dim)",
          foreground: "#ffffff",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;

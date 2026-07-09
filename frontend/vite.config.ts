import { fileURLToPath, URL } from "node:url";

import { defineConfig } from "vite";
import UnoCSS from "unocss/vite";
import vue from "@vitejs/plugin-vue";
import vueJsx from "@vitejs/plugin-vue-jsx";
import vueDevTools from "vite-plugin-vue-devtools";
import { visualizer } from "rollup-plugin-visualizer";

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    UnoCSS(),
    vue(),
    vueJsx(),
    vueDevTools(),
    visualizer({
      open: true,
      gzipSize: true,
      brotliSize: true,
    }),
  ],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 8080,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    chunkSizeWarningLimit: 5000,
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          if (id.includes("node_modules")) {
            if (id.includes("vue") || id.includes("pinia") || id.includes("vue-router")) {
              return "vue-core";
            }
            if (id.includes("naive-ui")) return "naive-ui";
            if (id.includes("@vue-flow")) return "vue-flow";
            if (id.includes("@iconify")) return "icons";
            if (id.includes("echarts")) return "echarts";
            if (id.includes("axios")) return "axios";
            if (id.includes("dayjs")) return "dayjs";
            if (id.includes("markdown") || id.includes("highlight")) return "markdown";
            return "vendor";
          }
        },
      },
    },
  },
});

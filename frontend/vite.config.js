import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Le backend FastAPI tourne sur :8420. On proxifie l'API et le WebSocket
// pour que le frontend appelle des chemins relatifs (/api, /ws).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 8421,
    host: true,
    proxy: {
      "/api": { target: "http://localhost:8420", changeOrigin: true },
      "/ws": { target: "ws://localhost:8420", ws: true },
    },
  },
});

# ─── Stage 1: builder ─────────────────────────────────────────────────────────
FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --prefer-offline

COPY . .
RUN npm run build

# ─── Stage 2: runtime (serve via Vite preview) ────────────────────────────────
FROM node:22-alpine AS runtime

WORKDIR /app

# Copy only the built assets + vite config needed for preview
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/vite.config.ts ./vite.config.ts

EXPOSE 5173

# Vite preview serves the production build on all interfaces
CMD ["npx", "vite", "preview", "--host", "0.0.0.0", "--port", "5173"]

# ============================================================
# JobPilot Frontend — Multi-Stage Dockerfile
# ============================================================

# ---------- Base Stage ----------
FROM node:20-alpine AS base
WORKDIR /app

# ---------- Dependencies Stage ----------
FROM base AS dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# ---------- Development Stage ----------
FROM dependencies AS development
COPY . .
EXPOSE 3000
ENV HOSTNAME="0.0.0.0"
CMD ["npm", "run", "dev"]

# ---------- Builder Stage ----------
FROM dependencies AS builder
COPY . .
RUN npm run build

# ---------- Production Stage ----------
FROM base AS production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
WORKDIR /app

# Copy built app and node_modules from builder stage
COPY --from=builder /app .

RUN chown -R nextjs:nodejs /app

USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
ENV NODE_ENV=production

CMD ["npm", "run", "start"]

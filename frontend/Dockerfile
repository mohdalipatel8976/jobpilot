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

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]

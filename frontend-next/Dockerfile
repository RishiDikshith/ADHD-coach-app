# ==========================================
# STAGE 1: Install Dependencies
# ==========================================
FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy lockfiles and package definitions
COPY package.json package-lock.json ./
RUN npm ci

# ==========================================
# STAGE 2: Build Application
# ==========================================
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Environment variables for build time
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
ENV NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_ENABLE_VOICE=true

RUN npm run build

# ==========================================
# STAGE 3: Production Runner
# ==========================================
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Create a secure system user for running the application
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy static public assets (must be copied individually since standalone leaves them out)
COPY --from=builder /app/public ./public

# Set the correct permissions for pre-rendered Next.js caches
RUN mkdir .next && chown nextjs:nodejs .next

# Leverage Next.js standalone bundle output
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Switch to the lightweight non-root user
USER nextjs

EXPOSE 3000

# Start Next.js using the standalone server
CMD ["node", "server.js"]

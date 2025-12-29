# 1. Base image
FROM node:18-alpine AS base
WORKDIR /app
COPY package*.json ./

# 2. Dependencies
FROM base AS deps
RUN npm ci

# 3. Development stage (Used by docker-compose locally)
FROM base AS development
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NODE_ENV=development
EXPOSE 3000
CMD ["npm", "run", "dev"]

# 4. Builder stage (for production)
FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# 5. Production runner stage (Used on your EC2)
FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# Copy only what is needed for standalone execution
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
ENV PORT 3000
CMD ["node", "server.js"]

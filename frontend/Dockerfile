# Use a Node.js 18 Alpine image as the base for building
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock)
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy the rest of your application code
COPY . .

# Build the Next.js application for production
RUN npm run build

# Use a lean Node.js 18 Alpine image for the final production image
WORKDIR /app

# Copy necessary files and directories from the builder stage
COPY --from=builder /app/.next ./.next/
COPY --from=builder /app/node_modules ./node_modules/
COPY --from=builder /app/public ./public/

# Explicitly copy single files to the current working directory ('.')
# This ensures the destination is always treated as a directory, preventing the error.
COPY --from=builder /app/package.json ./
COPY --from=builder /app/.env.production ./

EXPOSE 3000

CMD ["npm", "run", "start"]

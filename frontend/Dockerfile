# Use a Node.js 18 Alpine image as the base for building
FROM node:18-alpine AS builder

WORKDIR /app

# Only copy package.json and package-lock.json to install dependencies
COPY package*.json ./

# Install dependencies (including devDependencies needed for build)
RUN npm ci

# Copy the rest of your application code
# IMPORTANT: Ensure you have a .dockerignore file that excludes node_modules, .next, etc.
COPY . .

# Build the Next.js application for production
RUN npm run build

# Use a lean Node.js 18 Alpine image for the final production image
FROM node:18-alpine AS runner

WORKDIR /app

# Set environment variables for production
ENV NODE_ENV=production

# Copy the built application from the builder stage
# Only copy what's absolutely necessary for running the app
COPY --from=builder /app/.next ./.next/
COPY --from=builder /app/public ./public/

# If you have an .env.production file that's part of your build context, copy it
# Ensure this file is NOT sensitive and is for build-time env vars.
# If your ENV vars are purely runtime (from Docker Compose/EC2 user-data), you don't need this.
COPY --from=builder /app/.env.production ./

# Expose the port Next.js listens on
EXPOSE 3000

# Command to start the Next.js application in production mode
CMD ["npm", "run", "start"]

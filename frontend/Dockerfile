# Frontend Dockerfile (Production)
FROM node:18-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Set environment variables for build
ARG VITE_SUPABASE_URL=https://jhypmryyfafwwdkifgcg.supabase.co
ARG VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpoeXBtcnl5ZmFmd3dka2lmZ2NnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg4Mjg5MzgsImV4cCI6MjA4NDQwNDkzOH0.l9AUoJHeGeUL2VkG2lBRHzB_3cNzot-YDgg2PWzAdsw
ARG VITE_API_URL=http://189.126.105.51:8000
ARG VITE_API_VERSION=v1

ENV VITE_SUPABASE_URL=$VITE_SUPABASE_URL
ENV VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_API_VERSION=$VITE_API_VERSION

# Build application
RUN npm run build

# Production image
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]

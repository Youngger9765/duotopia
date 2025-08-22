# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

# Build with API URL
ARG VITE_API_URL=https://duotopia-backend-206313737181.asia-east1.run.app
ENV VITE_API_URL=$VITE_API_URL
RUN echo "Building with API URL: $VITE_API_URL"
RUN npm run build

# Production stage
FROM nginx:alpine

# Install gettext for envsubst
RUN apk add --no-cache gettext

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config template
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Cloud Run uses PORT environment variable
EXPOSE 8080

# Use envsubst to replace ${PORT} and then start nginx
CMD ["/bin/sh", "-c", "envsubst '${PORT}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
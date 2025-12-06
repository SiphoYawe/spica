# Development Dockerfile for Next.js
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Expose Next.js dev server port
EXPOSE 3000

# Set environment variable for API URL
ENV NEXT_PUBLIC_API_URL=http://localhost:8000

# Run dev server with hot reload
CMD ["npm", "run", "dev"]

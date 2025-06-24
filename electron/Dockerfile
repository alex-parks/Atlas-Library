# Blacksmith Atlas Electron Dockerfile
FROM node:18-alpine

# Install system dependencies for Electron
RUN apk add --no-cache \
    chromium \
    nss \
    freetype \
    freetype-dev \
    harfbuzz \
    ca-certificates \
    ttf-freefont \
    && rm -rf /var/cache/apk/*

# Set environment variables for Electron
ENV CHROME_BIN=/usr/bin/chromium-browser
ENV CHROME_PATH=/usr/lib/chromium/
ENV ELECTRON_CACHE=/root/.cache/electron
ENV ELECTRON_BUILDER_CACHE=/root/.cache/electron-builder

# Set working directory
WORKDIR /app

# Copy package files from the electron context
COPY package.json ./

# Install dependencies
RUN npm install

# Copy source code from the electron context
COPY . .

# Expose port (for web interface)
EXPOSE 3000

# Start Electron app
CMD ["npm", "start"] 
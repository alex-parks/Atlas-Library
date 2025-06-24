# Blacksmith Atlas Frontend Dockerfile
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json yarn.lock ./

# Install dependencies
RUN yarn install

# Copy source code
COPY . .

# Expose port
EXPOSE 3011

# Start development server
CMD ["yarn", "dev", "--port", "3011", "--host", "0.0.0.0"] 
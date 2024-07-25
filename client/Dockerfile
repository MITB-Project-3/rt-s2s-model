# Stage 1: Build the React app
FROM node:18 as build

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Clear npm cache
RUN npm cache clean --force

# Install dependencies
RUN npm install -g npm@10.8.1

# Set the npm registry to the default
RUN npm config set registry https://registry.npmjs.org/

# Remove node_modules and package-lock.json if they exist
RUN rm -rf node_modules package-lock.json

# Install dependencies
RUN npm install

# Copy the rest of the application source code
COPY . .

# Build the React app
RUN npm run build

# Stage 2: Serve the React app using nginx
FROM nginx:alpine

# Copy the built React app from the previous stage
COPY --from=build /app/build /usr/share/nginx/html

# Expose port 8080 (default for nginx)
EXPOSE 81

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

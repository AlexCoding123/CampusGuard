# 1. Base Stage
FROM node:24-bookworm AS base
WORKDIR /app

# 2. Dependencies Stage
FROM base AS deps
COPY package.json package-lock.json ./
# Best practice: use cache mounting
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# 3. Development Stage
FROM deps AS dev
COPY . .

# 4. Build Stage
FROM deps AS build
COPY . .
RUN npm run build

# 5. Production Stage
FROM nginx:alpine AS production
RUN touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid /var/cache/nginx /var/log/nginx /etc/nginx/conf.d
USER nginx
COPY --from=build /app/dist /usr/share/nginx/html
CMD ["nginx", "-g", "daemon off;"]
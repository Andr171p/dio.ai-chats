# syntax=docker/dockerfile:1
FROM node:24-bookworm-slim AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
COPY . .

ARG VITE_TRUSTED_ORIGINS=""
RUN VITE_AUTH_API_URL=/auth-api \
    VITE_CHATS_API_URL=/chats-api \
    VITE_TRUSTED_ORIGINS="$VITE_TRUSTED_ORIGINS" \
    npm run build

FROM nginx:stable-alpine AS runtime
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80

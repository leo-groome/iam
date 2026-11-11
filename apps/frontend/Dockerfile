FROM node:22-alpine AS build
WORKDIR /app
RUN npm install --global pnpm@10.11.0
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
# Only public browser configuration belongs in build arguments.
ARG PUBLIC_API_URL
ARG VITE_NEON_AUTH_URL
ENV PUBLIC_API_URL=$PUBLIC_API_URL VITE_NEON_AUTH_URL=$VITE_NEON_AUTH_URL
RUN test -n "$PUBLIC_API_URL" && test -n "$VITE_NEON_AUTH_URL" && pnpm build

FROM nginx:stable-alpine AS runtime
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80

FROM node:22-slim AS deps
WORKDIR /app
COPY frontend/dashboard/package.json frontend/dashboard/package-lock.json ./
RUN npm ci

FROM node:22-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/dashboard ./
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
RUN npm run build

FROM node:22-slim AS runner
WORKDIR /app
ENV NODE_ENV=production

RUN useradd --create-home --uid 1000 victoria
COPY --from=builder /app/public ./public
COPY --from=builder --chown=victoria:victoria /app/.next/standalone ./
COPY --from=builder --chown=victoria:victoria /app/.next/static ./.next/static
USER victoria

EXPOSE 3000
CMD ["node", "server.js"]

# Stage 1: Development
FROM node:20-alpine as development
WORKDIR /app
COPY package.json package-lock.json* ./
RUN --mount=type=cache,target=/root/.npm \
    if [ -f package-lock.json ]; then \
      npm ci --no-audit --no-fund; \
    else \
      npm install --no-audit --no-fund; \
    fi
COPY . .
ENV NITRO_PORT=3000
EXPOSE 3000
CMD ["npm","run","dev","--","-o"]

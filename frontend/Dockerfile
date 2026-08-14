FROM node:22-alpine

WORKDIR /app

RUN apk add --no-cache wget

COPY package*.json ./
RUN npm ci

COPY . .
RUN chmod +x scripts/dev-with-warmup.sh || true

# Toujours binder 0.0.0.0 (sinon inaccessible depuis Windows via le port publish)
CMD ["npm", "run", "dev"]

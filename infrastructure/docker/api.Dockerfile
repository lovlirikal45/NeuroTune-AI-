FROM node:22-alpine

WORKDIR /app

COPY . .

RUN corepack enable
RUN npm install -g pnpm
RUN pnpm install

CMD ["pnpm", "dev"]

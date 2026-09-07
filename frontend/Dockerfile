# ---- 构建阶段 ----
FROM node:20-slim AS builder
WORKDIR /app

# 利用 layer cache：先装依赖
COPY package*.json ./
RUN npm ci --silent

# 再复制源码并构建
COPY . .

# 构建时需要 NEXT_PUBLIC_API_BASE 环境变量（生产环境设为后端完整 URL）
# 本地构建不影响，Render 构建时由环境变量注入
RUN npm run build

# ---- 运行阶段 ----
FROM node:20-slim
WORKDIR /app

# 只复制构建产物 + 运行时依赖
COPY package*.json ./
RUN npm ci --omit=dev --silent

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.ts ./next.config.ts

EXPOSE 3000

CMD ["npm", "start", "--", "-p", "3000"]

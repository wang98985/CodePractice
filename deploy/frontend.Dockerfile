# 前端镜像：Node 构建静态文件 → Nginx 托管并反代后端
# 构建上下文为仓库根目录，故路径以 frontend/ 与 deploy/ 开头
FROM node:22-alpine AS build

WORKDIR /app

RUN npm config set registry https://registry.npmmirror.com

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
# 不注入 VITE_API_BASE_URL：前端默认走相对路径 /api，由 Nginx 反代到后端，天然无跨域问题
RUN npm run build

FROM nginx:1.27-alpine

COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
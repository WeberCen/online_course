# backend/Dockerfile

# 1. 使用官方的 Python 3.10 镜像作为基础
FROM python:3.10-slim

# 2. 设置环境变量，确保 Python 输出无缓冲
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. 设置工作目录
WORKDIR /app

# 4. 安装依赖
COPY requirements.txt /app/ 
RUN pip install --no-cache-dir -r requirements.txt

# 5. 复制项目代码
COPY . /app/
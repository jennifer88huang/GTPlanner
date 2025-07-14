# 使用官方Python基础镜像
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV UV_CACHE_DIR=/app/.uv-cache
ENV UV_LINK_MODE=copy

# 设置工作目录
WORKDIR /app

# 安装uv
RUN pip install --no-cache-dir uv

# 复制依赖文件
COPY pyproject.toml ./
COPY uv.lock ./  

# 使用uv安装Python依赖
RUN uv pip install --system -r pyproject.toml

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 11211

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:11211/health')" || exit 1

# 启动命令
CMD ["python", "fastapi_main.py"]
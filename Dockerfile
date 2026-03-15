# Asset-Lens Dockerfile
# 多阶段构建，优化镜像大小

# 第一阶段：构建阶段
FROM python:3.9-slim as builder

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir --user -r requirements.txt

# 第二阶段：运行阶段
FROM python:3.9-slim

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制 Python 包
COPY --from=builder /root/.local /root/.local

# 确保 Python 能找到安装的包
ENV PATH=/root/.local/bin:$PATH

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p /app/cache /app/data /app/logs /app/reports

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV ASSET_LENS_ENV=production

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -m asset_lens system check || exit 1

# 默认命令
CMD ["python", "-m", "asset_lens", "--help"]

# 标签
LABEL maintainer="Asset-Lens Team"
LABEL version="1.0.0"
LABEL description="Personal Asset Operating System"

# Asset-Lens Dockerfile
# 多阶段构建，优化镜像大小
# 使用华为云镜像加速

# 第一阶段：构建阶段
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/python:3.11-slim as builder

WORKDIR /app

# 使用阿里云镜像源
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN pip install --no-cache-dir uv

# 复制整个 InvestKit workspace
COPY pyproject.toml uv.lock ./
COPY investkit_utils investkit_utils
COPY asset-lens asset-lens

# 使用 uv 安装所有依赖（包含所有 extras），非 editable 模式
WORKDIR /app/asset-lens
RUN uv sync --all-extras --no-editable --frozen

# 第二阶段：运行阶段
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/python:3.11-slim

WORKDIR /app

# 使用阿里云镜像源
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y --no-install-recommends \
    curl \
    cron \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制虚拟环境
COPY --from=builder /app/asset-lens/.venv /app/.venv

# 设置环境变量使用虚拟环境
ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONUNBUFFERED=1
ENV ASSET_LENS_ENV=production

# 复制项目文件
COPY asset-lens .

# 创建必要的目录
RUN mkdir -p /app/cache /app/data /app/logs /app/reports

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -m asset_lens system check || exit 1

# 默认命令
CMD ["python", "-m", "asset_lens", "--help"]

# 标签
LABEL maintainer="InvestKit Team"
LABEL version="1.0.0"
LABEL description="Personal Asset Operating System"

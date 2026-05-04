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

# 使用官方 PyPI 源（最稳定）
RUN pip config set global.timeout 300 && \
    pip install --no-cache-dir --upgrade pip wheel setuptools

# 复制 investkit_utils 并安装
COPY investkit_utils /tmp/investkit_utils
RUN pip install --no-cache-dir --timeout 300 /tmp/investkit_utils && rm -rf /tmp/investkit_utils

# 复制依赖文件
COPY asset-lens/requirements-base.txt asset-lens/requirements-viz.txt asset-lens/requirements-web.txt asset-lens/requirements-data.txt asset-lens/requirements-ai.txt asset-lens/requirements-dev.txt ./

# 分批安装依赖（减少单次下载量，提高成功率）
# 1. 基础依赖
RUN pip install --no-cache-dir --timeout 300 -r requirements-base.txt || \
    pip install --no-cache-dir --timeout 300 -r requirements-base.txt

# 2. 可视化依赖
RUN pip install --no-cache-dir --timeout 300 -r requirements-viz.txt || \
    pip install --no-cache-dir --timeout 300 -r requirements-viz.txt

# 3. Web 依赖
RUN pip install --no-cache-dir --timeout 300 -r requirements-web.txt || \
    pip install --no-cache-dir --timeout 300 -r requirements-web.txt

# 4. 金融数据依赖
RUN pip install --no-cache-dir --timeout 300 -r requirements-data.txt || \
    pip install --no-cache-dir --timeout 300 -r requirements-data.txt

# 5. AI 依赖
RUN pip install --no-cache-dir --timeout 300 -r requirements-ai.txt || \
    pip install --no-cache-dir --timeout 300 -r requirements-ai.txt

# 6. 开发测试依赖
RUN pip install --no-cache-dir --timeout 300 -r requirements-dev.txt || \
    pip install --no-cache-dir --timeout 300 -r requirements-dev.txt

# 第二阶段：运行阶段
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/python:3.11-slim

WORKDIR /app

# 使用阿里云镜像源
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制 Python 包
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制项目文件
COPY asset-lens .

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
LABEL maintainer="InvestKit Team"
LABEL version="1.0.0"
LABEL description="Personal Asset Operating System"

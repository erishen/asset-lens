# syntax=docker/dockerfile:1
# asset-lens 运行镜像：CLI + 量化模块（quant）+ 可选 FastAPI Web
# 构建示例：docker build -t asset-lens:latest .
# 国内加速：docker build --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple -t asset-lens:latest .
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Shanghai

# git: investkit-utils 是 git 源；tzdata: TZ 生效；libgomp1: LightGBM/XGBoost 的 OpenMP 依赖。
RUN apt-get update \
 && apt-get install -y --no-install-recommends git tzdata libgomp1 \
 && ln -snf /usr/share/zoneinfo/${TZ} /etc/localtime \
 && echo ${TZ} > /etc/timezone \
 && rm -rf /var/lib/apt/lists/*

# 默认走官方源；国内网络可用 --build-arg PIP_INDEX_URL=镜像地址 覆盖。
ARG PIP_INDEX_URL=https://pypi.org/simple
ENV PIP_INDEX_URL=${PIP_INDEX_URL} \
    UV_INDEX_URL=${PIP_INDEX_URL}

WORKDIR /app

# pyproject.toml 声明了 readme = "README.md"，所以 README 必须进构建上下文。
COPY pyproject.toml uv.lock README.md ./
COPY asset_lens ./asset_lens

# investkit-utils 由 [tool.uv.sources] 映射为 git 源，pip 不读该配置 ⇒ 必须用 uv + uv.lock。
RUN python -m pip install --no-cache-dir uv \
 && uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

# 与 docker-compose.yml 的卷挂载一一对应，避免挂载时以 root 自动创建目录。
RUN mkdir -p cache data logs reports config

EXPOSE 8000

# 用项目自带且真实存在的自检命令（旧 compose 写的 `system check` 并不存在）。
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
    CMD ["python", "-m", "asset_lens", "check"]

# 默认保活并启动 Web API；跑 CLI 请用：
#   docker compose run --rm asset-lens python -m asset_lens --help
CMD ["uvicorn", "asset_lens.web.api:app", "--host", "0.0.0.0", "--port", "8000"]

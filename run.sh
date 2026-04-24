#!/bin/bash
# 运行 asset-lens 并过滤警告
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890

PYTHONWARNINGS=ignore /opt/anaconda3/envs/asset-lens/bin/python run.py "$@" 2>&1 | grep -v "ResourceWarning\|unclosed\|tracemalloc"

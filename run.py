#!/usr/bin/env python
"""
Asset Lens 启动脚本 - 过滤所有警告
"""
import atexit
import gc
import os
import sys
import warnings

# 设置代理
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'
os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'

os.environ['PYTHONWARNINGS'] = 'ignore'
warnings.filterwarnings('ignore')
warnings.simplefilter('ignore')


def cleanup():
    gc.collect()


atexit.register(cleanup)


if __name__ == '__main__':
    from asset_lens.cli import cli
    cli()
    gc.collect()

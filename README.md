<p align="center">
  <img src="docs/netherrack.svg" width="72" height="72" alt="netherrack">
</p>

<h1 align="center">netherrack</h1>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.160-009688?style=flat-square&logo=fastapi&logoColor=white">
  <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white">
  <img alt="React" src="https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black">
  <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript&logoColor=white">
</p>

## 简介

一个简洁的论坛。

## 快速开始

需要 Python 3.12+、Node 20+、PostgreSQL 14+（或已安装的 docker / podman）。

```bash
git clone git@github.com:fpg2012/netherrack.git
cd netherrack

# 1. 后端依赖与配置
cp backend/.env.example backend/.env
python3 -c "import secrets; print(secrets.token_hex(32))"   # 填进 .env 的 JWT_SECRET

make install

# 2. 数据库（docker → podman → 本地 pgserver 自动回退）
make db
make migrate

# 3. 起服务
make backend     # http://127.0.0.1:8000
make frontend    # http://localhost:5173
```

没有 docker 或拉不动镜像时，用 `make devdb` 起一个本地 PostgreSQL 16（无需 root）。

导入 Flarum 数据（需要把 dump 和附件放到 `data/` 下）：

```bash
make import      # 站上已有新帖时会拒绝执行，加 --force 才清空
make mentions    # 清理旧数据里的 @"name"#p123
make reindex     # 重建搜索分词
```

更多文档：

- 配置项、部署、多 worker 注意事项：[DEPLOY.md](DEPLOY.md)
- 代码结构、开发约定、测试、已知限制：[CONTRIBUTING.md](CONTRIBUTING.md)

## 许可证

本项目采用 [GNU General Public License v3.0 or later](LICENSE)（GPL-3.0-or-later）发布。

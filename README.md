# SignX（SaaS 企业运营管理平台）

SignX 是一个面向多租户场景的企业运营管理平台，后端基于 Flask + SQLAlchemy，内置 Web 控制台（Flask 模板 + 原生 JS），默认首页为 `/`。

## 系统功能说明

平台围绕「企业运营全流程」提供以下能力：

- **身份认证与权限体系**
  - 平台账号注册、登录、当前用户查询
  - 平台角色：`platform_admin` / `user`
  - 企业内角色：`owner` / `finance_manager` / `hr_manager` / `project_lead` / `member`
- **多租户企业管理**
  - 企业（租户）创建、查询、编辑
  - 企业维度数据隔离
- **员工与组织管理**
  - 员工信息管理、企业角色分配
- **项目与任务协同**
  - 项目管理、成员协作
  - 任务状态、优先级、依赖关系管理
- **财务与 AI Token 使用分析**
  - Token 使用记录
  - 收支与利润看板
- **工具中心与平台治理**
  - 工具中心接口（含 Openclaw 执行入口占位实现）
  - 平台侧租户、用户、审计日志管理

## API 概览（统一前缀 `/api/v1`）

- 认证：`/auth/register` `/auth/login` `/auth/me`
- 企业：`/companies`
- 员工：`/employees`
- 项目：`/projects` `/projects/{id}/tasks`
- 财务：`/finance/token-usage` `/finance/records` `/finance/dashboard`
- 工具：`/tools` `/tools/openclaw/execute`
- 平台管理：`/admin/tenants` `/admin/users` `/admin/audits`

## 正确的系统启动方式

### 方式一：本地 Python 启动（开发）

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python wsgi.py
```

启动后访问：

- 控制台首页：`http://127.0.0.1:5500/`
- 健康检查：`http://127.0.0.1:5500/healthz`

> `wsgi.py` 默认监听 `0.0.0.0:5500`。

### 方式二：Docker Build + Run

#### 1）构建镜像

```bash
docker build -t signx:latest .
```

#### 2）运行容器

```bash
docker run --rm -p 5500:5500 \
  -e DATABASE_URL=sqlite:////app/signx.db \
  -e SECRET_KEY=change-me \
  signx:latest
```

启动后访问：

- 控制台首页：`http://127.0.0.1:5500/`
- 健康检查：`http://127.0.0.1:5500/healthz`

> Docker 镜像默认使用 Gunicorn 启动：`gunicorn wsgi:app --bind 0.0.0.0:5500 --workers 4`。

### 方式三：Docker Compose 启动

```bash
docker compose up --build
```

访问地址：`http://127.0.0.1:5500/`

## 配置说明

- 默认数据库：`sqlite:///signx.db`（可通过 `DATABASE_URL` 覆盖）
- 默认密钥：`dev-secret`（建议通过 `SECRET_KEY` 覆盖）


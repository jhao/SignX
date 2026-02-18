# SignX（SaaS 企业运营管理平台）

本项目已按 `docs/saas_enterprise_platform_design.md` 重构为多租户 SaaS 企业运营管理平台后端（Flask + SQLAlchemy）。

## 核心能力

- 多租户企业管理（Company）
- 平台账号与角色（platform_admin / user）
- 员工与企业角色管理（owner / finance_manager / hr_manager / project_lead / member）
- 项目与任务协同（项目成员、任务依赖、优先级）
- AI Token 使用与财务看板（成本/收入/利润）
- 工具中心与 Openclaw 执行入口（占位实现）
- 审计日志（关键写操作记录）

## API 目录（统一前缀 `/api/v1`）

- 认证：`/auth/register` `/auth/login` `/auth/me`
- 企业：`/companies`
- 员工：`/employees`
- 项目：`/projects` `/projects/{id}/tasks`
- 财务：`/finance/token-usage` `/finance/records` `/finance/dashboard`
- 工具：`/tools` `/tools/openclaw/execute`
- 平台管理：`/admin/tenants` `/admin/users` `/admin/audits`

## 本地启动

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python wsgi.py
```

默认数据库：`sqlite:///signx.db`（可通过 `DATABASE_URL` 覆盖）。

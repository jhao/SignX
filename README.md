# SignX

SignX 是一套面向政企合同与批示流转场景的数字签批平台，围绕文档模板、审批链路、证据留痕和合规签名提供完整的业务闭环。系统以 Python 生态为核心，结合 LibreOffice 与 pyHanko 实现高保真渲染与高级电子签章，帮助业务部门快速完成协议拟制、流转、签署到归档的全流程管理。

## 核心能力

- **模板化制文**：支持建立带占位符的协议模板，可与业务系统数据打通，实现批量生成正式文档。
- **多角色审批与签署**：审批链可配置作者、复核、签署、抄送等角色，满足并行/串行混合流程与条件分支需求。
- **合规电子签章**：集成 pyHanko，支持高级电子签名、证书策略校验以及签章配置集中管理。
- **通知与提醒**：借助 APScheduler 驱动定时任务，按流程节点发送邮件提醒、超期告警与结果通知。
- **审计与留痕**：关键操作写入事件审计表，保留时间戳、操作者、来源 IP 等信息，支持导出合规报告。
- **文档存储管理**：签署成品统一存放在文件存储目录或对象存储中，提供版本留存与生命周期控制能力。
- **系统集成扩展**：提供 RESTful API 与 Webhook，可供外部业务系统发起签署、监听流程状态与获取归档件。

## 系统架构概览

当前代码以 Flask 单体应用为主体，围绕以下逻辑层次组织：

1. **接口层**：由 Flask Blueprint/视图函数组成，负责路由、鉴权与请求校验，向外提供 REST API 与必要的实时通道。
2. **应用服务层**：封装模板生成、签章编排、流程控制、通知派发等领域服务逻辑，屏蔽底层资源细节。
3. **数据访问层**：基于 SQLAlchemy 定义模型与仓储，Alembic 管理 MySQL 迁移，确保结构演进可控。
4. **调度与任务层**：集中维护 APScheduler 作业、后台任务及与外部队列/执行器的衔接，实现通知、超期检查等自动化流程。
5. **基础设施层**：聚合文件存储适配器、邮件网关、身份接入、配置读取等通用组件，支撑上层业务能力。

> 提示：若团队维护独立的前端工程（如基于 Vite + TypeScript 的 SPA），可在对应仓库完成构建后将产物部署至反向代理或由 Flask 提供静态资源。本仓库聚焦后端服务，可在无前端依赖的情况下正常运行。

## 开发环境准备

1. **安装依赖工具**
   - Python 3.11
   - MySQL 8.x（可本机安装或使用容器）
   - LibreOffice（用于文档渲染）与 `pyHanko` CLI（用于高级签章）
   - Node.js 18+ 与 npm（如需在独立前端仓库编译 Web 客户端）

2. **克隆项目**
   ```bash
   git clone <repository-url>
   cd SignX
   ```

3. **创建并激活 Python 虚拟环境**
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate  # Windows 使用 .venv\Scripts\activate
   ```

4. **安装后端依赖**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **安装前端依赖（如需）**
   - 若项目启用独立前端，请在对应仓库执行 `npm install`、`npm run build`，并将产物部署到反向代理或复制到后端静态目录。
   - 若仅调试后端 API，可跳过此步骤。

6. **初始化数据库**
   - 创建数据库（如 `signx_dev`）与具备读写权限的用户。
   - 在 `.env` 中配置连接串（见下文配置章节）。

7. **执行数据库迁移**
   ```bash
   alembic upgrade head
   ```

8. **初始化基础数据**
   ```bash
   flask seed init  # 根据项目内实际种子脚本调整命令
   ```

9. **启动开发服务**
   ```bash
   flask run
   # 或使用 gunicorn 进行类生产验证
   gunicorn "signx.app:create_app()" --bind 0.0.0.0:8000 --workers 4
   ```

## 配置说明

项目通过 `.env` 管理敏感配置，常用变量如下：

| 变量 | 说明 | 示例 |
| --- | --- | --- |
| `FLASK_ENV` | 运行环境（development/production） | `development` |
| `SECRET_KEY` | Flask 会话与 CSRF 密钥 | `change-me` |
| `DATABASE_URL` | SQLAlchemy 连接串 | `mysql+pymysql://user:pass@localhost:3306/signx_dev` |
| `STORAGE_BACKEND` | 文件存储实现（`local`/`s3` 等） | `local` |
| `STORAGE_PATH` | 本地存储根目录 | `/var/signx/storage` |
| `S3_BUCKET` | 使用 S3 兼容存储时的桶名 | `signx-documents` |
| `MAIL_SERVER` | SMTP 主机 | `smtp.example.com` |
| `MAIL_PORT` | SMTP 端口 | `587` |
| `MAIL_USERNAME` | SMTP 用户名 | `noreply@example.com` |
| `MAIL_PASSWORD` | SMTP 密码 | `super-secret` |
| `MAIL_USE_TLS` | 是否启用 TLS | `true` |
| `APSCHEDULER_JOBSTORES` | APScheduler JobStore 配置 | `{ "default": { "type": "sqlalchemy", "url": "sqlite:///jobs.sqlite" } }` |
| `APSCHEDULER_EXECUTORS` | APScheduler 执行器配置 | `{ "default": { "type": "threadpool", "max_workers": 10 } }` |
| `APSCHEDULER_TIMEZONE` | 调度使用的时区 | `UTC` |
| `PYHANKO_CONFIG` | pyHanko 配置文件路径 | `/etc/signx/pyhanko.yml` |
| `LIBREOFFICE_PATH` | LibreOffice 可执行路径 | `/usr/bin/libreoffice` |
| `FRONTEND_DIST_DIR` | 前端打包产物目录 | `frontend/dist` |
| `FILE_STORAGE_ROOT` | 持久化文件目录（如与 STORAGE_PATH 区分使用） | `/data/signx/files` |
| `OIDC_ISSUER` | 若启用 OIDC 认证，需提供的发行者地址 | `https://id.example.com` |

**示例 `.env`：**

```env
FLASK_ENV=development
SECRET_KEY=change-me
DATABASE_URL=mysql+pymysql://signx:password@localhost:3306/signx_dev
STORAGE_BACKEND=local
STORAGE_PATH=/var/signx/storage
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=noreply@example.com
MAIL_PASSWORD=super-secret
MAIL_USE_TLS=true
APSCHEDULER_JOBSTORES={"default":{"type":"sqlalchemy","url":"sqlite:///jobs.sqlite"}}
APSCHEDULER_EXECUTORS={"default":{"type":"threadpool","max_workers":10}}
APSCHEDULER_TIMEZONE=UTC
PYHANKO_CONFIG=config/pyhanko.yml
LIBREOFFICE_PATH=/usr/bin/libreoffice
FRONTEND_DIST_DIR=frontend/dist
FILE_STORAGE_ROOT=/data/signx/files
OIDC_ISSUER=https://id.example.com
```

确保文件存储目录具备写权限，并在生产环境中挂载持久卷或对象存储服务。

## Docker / Docker Compose

1. **构建镜像**
   ```bash
   docker compose build
   ```

2. **启动服务**
   ```bash
   docker compose up -d
   ```

   Compose 默认会启动应用容器、MySQL 与所需的调度/辅助组件，可在 `docker-compose.override.yml` 中覆盖配置。

3. **数据卷说明**
   - `signx_db_data`：持久化 MySQL 数据。
   - `signx_storage`：存放签署成品与相关附件。

4. **健康检查**
   - 应用：`curl http://localhost:8000/health` 应返回 200。
   - 数据库：`docker compose exec db mysqladmin ping -h localhost`。
   - 调度：检查 `docker compose logs scheduler` 确认任务正常加载。

5. **常见问题排查**
   - **迁移未执行**：`docker compose exec app alembic upgrade head`。
   - **调度任务未启动**：核对 `.env` 中 APScheduler 配置与数据库连通性。
   - **缺少证书或签章配置**：确保 pyHanko 配置文件与证书目录通过卷正确挂载。
   - **LibreOffice 不可用**：确认镜像中已安装 LibreOffice，或在 Compose 中添加对应安装步骤。

6. **停止与清理**
   ```bash
   docker compose down
   docker compose down -v  # 如需同时清理数据卷
   ```

## 测试与质量保障

- **单元测试/集成测试**：
  ```bash
  pytest
  ```
- **静态检查与格式化**：
  ```bash
  ruff check
  ruff format  # 或 black、isort 等项目约定工具
  ```
- **类型检查（如使用）**：
  ```bash
  mypy signx
  ```

建议在提交代码前运行上述命令，配合 CI/CD 平台自动执行测试与质量检查。

## 部署建议

- 在生产环境使用 `gunicorn` + `gevent` 等多进程/协程模型，并放置于反向代理（Nginx）之后。
- 使用 MySQL 主从或托管数据库服务，结合定期备份机制保障数据安全。
- 将文件存储目录迁移至对象存储（如 S3/OSS），并配置生命周期策略。
- 通过 Vault、AWS Secrets Manager 等安全管理敏感配置；禁用在代码仓库存储 `.env`。
- 配置 Prometheus/Grafana 收集应用与数据库指标，结合 Loki/ELK 进行日志集中化。
- 对外提供回调接口时，建议启用签名校验与 IP 白名单，避免非法调用。


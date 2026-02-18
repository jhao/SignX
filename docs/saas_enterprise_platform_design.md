# SaaS 企业运营管理平台设计方案

## 1. 背景与目标

本方案面向中小企业（SMB）构建多租户 SaaS 企业运营管理平台，帮助企业快速搭建自己的数字化管理空间，覆盖以下核心业务：

- 企业创建与组织配置
- 员工与角色管理
- 项目与任务协同
- AI 调用成本与财务驾驶舱
- 工具链集成（含 MCP / Openclaw）

目标是在“可扩展、可配置、可审计”的前提下，提供简洁、国际化、低认知负担的产品体验。

---

## 2. 产品定位与业务价值

### 2.1 目标客户

- 处于数字化升级阶段的中小企业
- 需要跨团队协作、项目过程可追踪的业务团队
- 对 AI 成本可视化与利润分析有明确需求的管理层

### 2.2 核心价值

- **统一管理入口**：公司、员工、项目、财务、工具在同一平台中联动。
- **多租户安全隔离**：企业数据默认隔离，支持更高隔离等级扩展。
- **精细化权限治理**：平台管理员、企业老板、项目负责人、员工的权限分层清晰。
- **可扩展架构**：支持后续引入更多 AI 服务商、行业插件和自动化能力。

---

## 3. 多租户架构设计

### 3.1 租户模型

- 一个企业 = 一个租户（Tenant）
- 一个租户可包含多个用户、员工、项目、工具和财务记录
- 用户可创建公司或受邀加入公司

### 3.2 数据隔离策略（分级）

1. **逻辑隔离（默认）**
   - 单数据库共享 Schema，通过 `company_id` / `tenant_id` 实现数据隔离。
   - 配合后端统一租户过滤中间件，避免跨租户读取。

2. **Schema 隔离（增强）**
   - 每个租户独立数据库 Schema。
   - 适用于数据治理要求更高客户。

3. **数据库实例隔离（高级）**
   - 每个租户独立数据库实例。
   - 适用于高合规、高安全等级客户。

> 建议从逻辑隔离起步，预留向上迁移能力（租户路由、迁移脚本、备份策略）。

### 3.3 权限模型

建议采用 **RBAC + 数据域约束（ABAC）**：

- 平台级角色：`platform_admin`
- 企业级角色：`owner`、`finance_manager`、`hr_manager`
- 项目级角色：`project_lead`、`member`
- 数据域约束：角色 + `company_id` + 项目成员关系共同判定最终访问权限。

---

## 4. 技术栈与工程建议

## 4.1 后端

推荐：**Python + FastAPI（或 Django）**

- FastAPI：高性能、类型提示完善、API 文档自动生成。
- Django：后台能力完整、适合 CRUD 密集业务。

建议组件：

- ORM：SQLAlchemy（Django 则用 Django ORM）
- 认证：JWT + Refresh Token + 可选 MFA
- 任务队列：Celery / RQ（用于异步统计、通知、报表计算）
- 配置：Pydantic Settings / Django settings + dotenv

### 4.2 前端

推荐：**React + TypeScript + 组件库（如 Fluent UI）**

- 单页应用（SPA）
- 响应式布局（移动优先）
- 状态管理：Zustand/Redux（按团队习惯）
- 图表：ECharts / Recharts（用于财务看板）

### 4.3 数据与存储

- 数据库：SQLite（开发）、PostgreSQL/MySQL（生产）
- 迁移工具：Alembic（或 Django Migrations）
- 文件存储：本地文件系统（后续可抽象为对象存储）

### 4.4 运维与部署

- 容器化：Docker
- 编排：Kubernetes
- 监控：Prometheus + Grafana
- 日志：ELK / Loki
- 告警：Alertmanager

---

## 5. 功能模块设计

## 5.1 企业创建与配置

字段建议：

- 公司名称、业务模式、企业目标
- 主营业务描述、记账方式、组织结构
- 注册资本、税务计算描述

设计要点：

- 按“基础信息 / 财务制度 / 组织结构”分区
- 高优字段前置，低频字段折叠（渐进披露）
- 未分配岗位以空位卡片提示，促进组织完善

## 5.2 员工管理

能力范围：

- 卡片式员工列表（头像、职责、角色）
- AI 服务配置（Gemini/OpenAI/Claude/DeepSeek/Kimi/ChatGLM/自定义）
- 多项目参与与角色展示

设计要点：

- 默认只展示必要字段
- 高级设置（API 地址、参数、Key）折叠展示
- 对敏感字段（Secret Key）脱敏 + 二次确认

## 5.3 项目管理

能力范围：

- 项目创建（目标、周期、负责人、所需人员）
- 任务拆解（责任人、截止日期、优先级、依赖关系）
- 多视图（看板 / 甘特图 / 列表）

设计要点：

- 鼓励将目标拆解为可执行任务
- 明确负责人和时间边界
- 支持过滤、排序、钻取分析

## 5.4 财务看板

能力范围：

- AI 调用次数、Token 消耗、成本统计
- 项目收入/成本/利润归集
- 异常预警（成本超标、利润异常）

设计要点：

- 关键 KPI 首屏展示
- 提供“上次更新时间”与刷新策略
- 条件格式高亮异常，减少管理盲区

## 5.5 公司工具与自动化

能力范围：

- 工具注册与配置（浏览器、本地软件、第三方系统）
- MCP 标准接入
- Openclaw 自动化任务执行

权限策略：

- 工具访问按“员工/角色”双层授权
- 高风险工具操作记录审计日志

## 5.6 用户与管理员管理

- 注册登录：邮箱/手机号 + 验证码/邮件验证
- 密码重置与设备登录管理
- 平台管理员支持租户审核、全局统计、权限巡检

---

## 6. 数据模型建议（逻辑层）

| 实体 | 关键字段 | 说明 |
| --- | --- | --- |
| Company | id, name, business_model, description, accounting_method, capital, tax_info | 企业基础信息 |
| Role | id, company_id, name, responsibilities | 组织角色 |
| Employee | id, company_id, name, primary_tasks, role_id, ai_provider, api_key, photo_path | 员工与 AI 配置 |
| Project | id, company_id, name, description, lead_id, start_date, end_date, objective | 项目实体 |
| Task | id, project_id, assignee_id, description, status, due_date, priority | 任务实体 |
| TokenUsage | id, company_id, model, tokens_used, cost, date | AI 消耗记录 |
| FinancialRecord | id, company_id, date, description, amount, type | 财务流水 |
| Tool | id, company_id, name, description, config, supported_by_mcp | 工具配置 |
| UserAccount | id, email, password_hash, platform_role, company_id | 平台账户 |
| ProjectEmployee | project_id, employee_id, role_in_project | 项目-员工多对多 |

补充建议：

- 所有核心实体应包含 `created_at`、`updated_at`、`created_by` 字段。
- 建议增加 `AuditLog` 表记录关键操作。
- `api_key` 建议加密存储（KMS 或应用层加密）。

---

## 7. API 设计原则

- RESTful 资源命名，统一前缀 `/api/v1`
- 统一返回结构（`code/message/data`）
- 分页、过滤、排序标准化
- 幂等性保障（创建接口支持 `Idempotency-Key`）
- OpenAPI 文档自动生成

示例接口分组：

- `POST /auth/register`
- `POST /companies`
- `GET /employees?company_id=...`
- `POST /projects/{id}/tasks`
- `GET /finance/dashboard?range=30d`
- `POST /tools/openclaw/execute`

---

## 8. UI/UX 与设计系统规范

### 8.1 视觉风格

- 参考微软 / Azure 设计体系
- 中性色 + 品牌主色，避免高饱和混用
- 标题、正文、辅助文本采用统一排版层级

### 8.2 交互原则

- “不要让我思考”：流程短、路径清
- 渐进披露：默认简单，高级可展开
- 反馈即时：保存成功、错误提示、加载态可见

### 8.3 可访问性（WCAG 2.1 AA）

- 键盘可达、焦点可见
- 图片和图表提供文本替代
- 色彩对比满足可读性要求

### 8.4 响应式策略

- 采用移动优先
- 小屏优先信息摘要，大屏增强分析能力

---

## 9. 安全与合规设计

- 最小权限原则（PoLP）
- 多租户强制过滤（后端与数据库双重约束）
- 密码哈希（Argon2/bcrypt）+ 登录风控
- 机密信息加密（API Key、访问令牌）
- 全链路审计日志与可追溯性
- 备份、灾备、恢复演练制度化

---

## 10. 实施路线图（里程碑）

### 阶段 1：MVP（4~6 周）

- 用户注册登录
- 公司创建与基础配置
- 员工管理
- 项目与任务基础能力

### 阶段 2：核心增强（4~8 周）

- AI 接口接入与 token 成本统计
- 财务看板（基础版）
- 工具中心与 MCP 接入

### 阶段 3：企业级能力（6~10 周）

- Openclaw 自动化
- 高级权限模型与审计报表
- 多隔离级别支持（Schema/实例）
- 高可用部署与自动伸缩

### 阶段 4：持续优化

- 用户行为分析与体验迭代
- 性能优化与成本治理
- 插件生态与行业模板扩展

---

## 11. 测试与质量保障

- 单元测试：核心服务、权限、计费逻辑
- 集成测试：关键业务链路（建企-建项-分配-统计）
- E2E 测试：高价值用户场景
- 安全测试：鉴权绕过、越权访问、敏感信息泄露
- 性能测试：并发访问、看板查询、批量任务执行

建议 CI/CD 门禁：

- 测试通过率阈值
- 代码扫描（SAST/依赖漏洞）
- 数据库迁移脚本校验

---

## 12. 结论

该方案以多租户架构为核心，通过标准化模块（企业、员工、项目、财务、工具）构建可持续扩展的 SaaS 平台。通过统一设计系统、分层权限、可观测运维和智能预警机制，平台可在保证易用性的同时满足企业级管理深度。

后续新增能力（行业方案、Agent 自动化、更多 AI 模型）可在既有模块边界内平滑扩展，降低长期演进成本。

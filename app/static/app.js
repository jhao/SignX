const state = {
  me: null,
  companyId: null,
  lang: 'zh',
  activeView: 'auth',
  projects: [],
};

const i18n = {
  zh: {
    auth: '认证',
    companies: '企业配置',
    employees: '员工管理',
    projects: '项目任务',
    finance: '财务看板',
    tools: '工具自动化',
    admin: '平台管理',
    pleaseLogin: '请先注册或登录。',
    loggedIn: '已登录：',
    noCompany: '当前账号尚未绑定企业，请先创建企业。',
  },
  en: {
    auth: 'Auth',
    companies: 'Company',
    employees: 'Employees',
    projects: 'Projects',
    finance: 'Finance',
    tools: 'Tools',
    admin: 'Admin',
    pleaseLogin: 'Please register or login first.',
    loggedIn: 'Logged in as: ',
    noCompany: 'No tenant linked yet. Create a company first.',
  },
};

const views = [
  { key: 'auth', secured: false },
  { key: 'companies', secured: true },
  { key: 'employees', secured: true },
  { key: 'projects', secured: true },
  { key: 'finance', secured: true },
  { key: 'tools', secured: true },
  { key: 'admin', secured: true },
];

const navTabs = document.getElementById('navTabs');
const statusBar = document.getElementById('statusBar');

function t(key) {
  return i18n[state.lang][key] || key;
}

function setStatus(message, isError = false) {
  statusBar.textContent = message;
  statusBar.classList.toggle('error', isError);
}

async function api(path, method = 'GET', payload) {
  const res = await fetch(`/api/v1${path}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: payload ? JSON.stringify(payload) : undefined,
  });

  let json = null;
  try {
    json = await res.json();
  } catch {
    json = { message: 'Invalid response' };
  }

  if (!res.ok || json.code !== 0) {
    throw new Error(json.message || `Request failed: ${res.status}`);
  }
  return json.data;
}

function renderNav() {
  navTabs.innerHTML = '';
  views.forEach((v) => {
    const btn = document.createElement('button');
    btn.className = `nav-btn ${state.activeView === v.key ? 'active' : ''}`;
    btn.textContent = t(v.key);
    btn.onclick = () => {
      if (v.secured && !state.me) {
        setStatus(t('pleaseLogin'), true);
        state.activeView = 'auth';
      } else {
        state.activeView = v.key;
      }
      renderAll();
    };
    navTabs.appendChild(btn);
  });
}

function switchView() {
  views.forEach((v) => {
    document.getElementById(`view-${v.key}`).classList.toggle('hidden', state.activeView !== v.key);
  });
}

function card(html) {
  const c = document.getElementById('cardTemplate').content.firstElementChild.cloneNode(true);
  c.innerHTML = html;
  return c;
}

function renderAuth() {
  const el = document.getElementById('view-auth');
  el.innerHTML = '';

  el.appendChild(
    card(`
      <h3>登录 / 注册</h3>
      <div class="grid">
        <form id="registerForm" class="item">
          <h4>注册账号</h4>
          <label>邮箱</label><input name="email" type="email" required />
          <label>姓名</label><input name="full_name" required />
          <label>密码</label><input name="password" type="password" required />
          <label>平台角色</label>
          <select name="platform_role">
            <option value="user">user</option>
            <option value="platform_admin">platform_admin</option>
          </select>
          <button class="primary-btn" type="submit">注册</button>
        </form>

        <form id="loginForm" class="item">
          <h4>登录</h4>
          <label>邮箱</label><input name="email" type="email" required />
          <label>密码</label><input name="password" type="password" required />
          <button class="primary-btn" type="submit">登录</button>
        </form>
      </div>
    `),
  );

  const registerForm = document.getElementById('registerForm');
  registerForm.onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(registerForm);
    try {
      await api('/auth/register', 'POST', Object.fromEntries(fd.entries()));
      setStatus('注册成功，请登录。');
      registerForm.reset();
    } catch (err) {
      setStatus(err.message, true);
    }
  };

  const loginForm = document.getElementById('loginForm');
  loginForm.onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(loginForm);
    try {
      state.me = await api('/auth/login', 'POST', Object.fromEntries(fd.entries()));
      state.companyId = state.me.company_id || null;
      setStatus(`${t('loggedIn')}${state.me.email}`);
      state.activeView = 'companies';
      await renderAll();
    } catch (err) {
      setStatus(err.message, true);
    }
  };
}

async function renderCompanies() {
  const el = document.getElementById('view-companies');
  el.innerHTML = '';
  let companies = [];
  try {
    companies = await api('/companies');
    if (companies.length > 0 && !state.companyId) {
      state.companyId = companies[0].id;
    }
  } catch (err) {
    setStatus(err.message, true);
    return;
  }

  el.appendChild(
    card(`
      <h3>企业创建与组织配置</h3>
      <p class="small">按“基础信息 / 财务制度 / 组织结构”填写，低频字段可后补。</p>
      <form id="companyForm" class="grid">
        <input type="hidden" name="editing_company_id" />
        <div class="item">
          <h4>基础信息</h4>
          <label>公司名称</label><input name="name" required />
          <label>业务模式</label><input name="business_model" />
          <label>企业目标</label><textarea name="goals"></textarea>
          <label>主营业务描述</label><textarea name="description"></textarea>
        </div>
        <div class="item">
          <h4>财务制度</h4>
          <label>记账方式</label><input name="accounting_method" />
          <label>注册资本</label><input name="capital" type="number" step="0.01" />
          <label>税务计算描述</label><textarea name="tax_info"></textarea>
        </div>
        <div class="item">
          <h4>组织结构</h4>
          <label>组织结构（结构化JSON）</label><textarea name="organization_structure" placeholder="[{"name":"研发负责人","description":"负责研发管理"}]"></textarea>
          <label>组织结构（批量编辑，每行：角色|描述）</label><textarea name="organization_structure_lines" placeholder="研发负责人|负责技术路线与研发推进\n产品经理|负责需求分析与产品规划"></textarea>
          <button class="primary-btn" type="submit">保存企业</button>
          <button class="secondary-btn" id="clearCompanyEdit" type="button">清空编辑</button>
        </div>
      </form>
    `),
  );

  const listCard = card('<h3>企业列表</h3><div id="companyList" class="data-list"></div>');
  el.appendChild(listCard);
  const listEl = listCard.querySelector('#companyList');
  listEl.innerHTML = companies
    .map(
      (c) => `<div class="item">
        <strong>${c.name}</strong>
        <div class="small">模式：${c.business_model || '未填写'} | 记账：${c.accounting_method || '未填写'}</div>
        <button data-company="${c.id}" class="secondary-btn pick-company">设为当前企业</button>
        <button data-edit-company="${c.id}" class="secondary-btn edit-company">编辑</button>
      </div>`,
    )
    .join('');

  const form = document.getElementById('companyForm');
  listEl.querySelectorAll('.pick-company').forEach((btn) => {
    btn.onclick = () => {
      state.companyId = Number(btn.dataset.company);
      setStatus(`已切换当前企业：${state.companyId}`);
    };
  });
  listEl.querySelectorAll('.edit-company').forEach((btn) => {
    btn.onclick = async () => {
      try {
        const detail = await api(`/companies/${Number(btn.dataset.editCompany)}`);
        Object.entries(detail).forEach(([k, v]) => {
          if (form.elements[k]) form.elements[k].value = v || '';
        });
        form.elements.organization_structure_lines.value = (detail.organization_structure_items || []).map((item) => `${item.name}|${item.description || ''}`).join('\n');
        form.elements.editing_company_id.value = detail.id;
        setStatus(`正在编辑企业：${detail.name}`);
      } catch (err) {
        setStatus(err.message, true);
      }
    };
  });

  document.getElementById('clearCompanyEdit').onclick = () => {
    form.reset();
    form.elements.editing_company_id.value = '';
  };

  form.onsubmit = async (e) => {
    e.preventDefault();
    const payload = Object.fromEntries(new FormData(e.target).entries());
    const editingId = payload.editing_company_id;
    delete payload.editing_company_id;
    try {
      if (editingId) {
        await api(`/companies/${editingId}`, 'PUT', payload);
        setStatus(`企业 #${editingId} 更新成功`);
      } else {
        const company = await api('/companies', 'POST', payload);
        state.companyId = company.id;
        setStatus(`企业创建成功：${company.name}`);
      }
      await renderCompanies();
    } catch (err) {
      setStatus(err.message, true);
    }
  };
}

async function renderEmployees() {
  const el = document.getElementById('view-employees');
  el.innerHTML = '';
  if (!state.companyId) {
    el.appendChild(card(`<h3>${t('noCompany')}</h3>`));
    return;
  }

  let employees = [];
  let organizationRoles = [];
  try {
    [employees, organizationRoles] = await Promise.all([
      api(`/employees?company_id=${state.companyId}`),
      api(`/employees/organization-roles?company_id=${state.companyId}`),
    ]);
  } catch (err) {
    setStatus(err.message, true);
  }

  el.appendChild(
    card(`
      <h3>员工与角色管理</h3>
      <form id="employeeForm" class="grid">
        <input type="hidden" name="editing_employee_id" />
        <div class="item">
          <label>姓名</label><input name="name" required />
          <label>岗位职责</label><textarea name="primary_tasks"></textarea>
          <label>组织机构角色</label>
          <select name="organization_role" id="organizationRoleSelect"><option value="">请选择</option></select>
          <label>公司角色（系统权限）</label>
          <select name="company_role">
            <option value="owner">owner</option><option value="finance_manager">finance_manager</option><option value="hr_manager">hr_manager</option><option value="project_lead">project_lead</option><option value="member" selected>member</option>
          </select>
        </div>
        <div class="item">
          <label>AI 服务商</label><input name="ai_provider" />
          <label>智能体提示词</label><textarea name="agent_prompt"></textarea>
          <button class="secondary-btn" id="generatePromptBtn" type="button">AI 生成提示词</button>
          <button class="primary-btn" type="submit">保存员工</button>
          <button class="secondary-btn" id="clearEmployeeEdit" type="button">清空编辑</button>
        </div>
      </form>
    `),
  );

  const list = card('<h3>员工列表</h3><div id="employeeList" class="data-list"></div>');
  list.querySelector('#employeeList').innerHTML = employees
    .map(
      (e) => `<div class="item"><strong>${e.name}</strong> <span class="tag">${e.organization_role || e.company_role}</span>
      <div class="small">职责：${e.primary_tasks || '未填写'}</div>
      <div class="small">Prompt：${e.agent_prompt || '未生成'}</div>
      <button class="secondary-btn edit-employee" data-id="${e.id}">编辑</button></div>`,
    )
    .join('');
  el.appendChild(list);

  const form = document.getElementById('employeeForm');
  const roleSelect = document.getElementById('organizationRoleSelect');
  roleSelect.innerHTML = '<option value="">请选择</option>' + organizationRoles.map((role) => `<option value="${role.name}">${role.name}（${role.description || '无描述'}）</option>`).join('');
  const fillForm = (employee) => {
    form.elements.editing_employee_id.value = employee.id;
    form.elements.name.value = employee.name || '';
    form.elements.primary_tasks.value = employee.primary_tasks || '';
    form.elements.company_role.value = employee.company_role || 'member';
    form.elements.organization_role.value = employee.organization_role || '';
    form.elements.ai_provider.value = employee.ai_provider || '';
    form.elements.agent_prompt.value = employee.agent_prompt || '';
  };

  list.querySelectorAll('.edit-employee').forEach((btn) => {
    btn.onclick = () => {
      const target = employees.find((e) => e.id === Number(btn.dataset.id));
      if (!target) return;
      fillForm(target);
      setStatus(`正在编辑员工：${target.name}`);
    };
  });

  document.getElementById('generatePromptBtn').onclick = async () => {
    const payload = Object.fromEntries(new FormData(form).entries());
    payload.company_id = state.companyId;
    payload.generate_agent_prompt = true;
    try {
      if (payload.editing_employee_id) {
        const result = await api(`/employees/${payload.editing_employee_id}`, 'PUT', payload);
        form.elements.agent_prompt.value = result.agent_prompt || '';
      } else {
        const created = await api('/employees', 'POST', payload);
        form.elements.editing_employee_id.value = created.id;
        form.elements.agent_prompt.value = created.agent_prompt || '';
      }
      setStatus('AI 提示词已生成');
      await renderEmployees();
    } catch (err) {
      setStatus(err.message === 'ai_model_not_configured' ? '系统AI模型未配置，请先在系统设置中配置。' : err.message, true);
    }
  };

  document.getElementById('clearEmployeeEdit').onclick = () => {
    form.reset();
    form.elements.editing_employee_id.value = '';
  };

  form.onsubmit = async (evt) => {
    evt.preventDefault();
    const payload = Object.fromEntries(new FormData(evt.target).entries());
    payload.company_id = state.companyId;
    const editingId = payload.editing_employee_id;
    delete payload.editing_employee_id;
    try {
      if (editingId) {
        await api(`/employees/${editingId}`, 'PUT', payload);
        setStatus('员工更新成功');
      } else {
        await api('/employees', 'POST', payload);
        setStatus('员工创建成功');
      }
      await renderEmployees();
    } catch (err) {
      setStatus(err.message, true);
    }
  };
}

async function renderProjects() {
  const el = document.getElementById('view-projects');
  el.innerHTML = '';
  if (!state.companyId) {
    el.appendChild(card(`<h3>${t('noCompany')}</h3>`));
    return;
  }

  let employees = [];
  try {
    [state.projects, employees] = await Promise.all([
      api(`/projects?company_id=${state.companyId}`),
      api(`/employees?company_id=${state.companyId}`),
    ]);
  } catch (err) {
    setStatus(err.message, true);
    return;
  }

  const employeeOptions = employees.map((e) => `<option value="${e.id}">${e.name}（${e.organization_role || e.company_role}）</option>`).join('');

  el.appendChild(
    card(`
      <h3>项目与任务协同</h3>
      <div class="grid">
        <form id="projectForm" class="item">
          <h4>创建项目</h4>
          <label>项目名称</label><input name="name" required />
          <label>项目目标</label><textarea name="objective"></textarea>
          <label>负责人</label><select name="lead_id"><option value="">未分配</option>${employeeOptions}</select>
          <label>开始日期</label><input name="start_date" type="datetime-local" />
          <label>结束日期</label><input name="end_date" type="datetime-local" />
          <label>描述</label><textarea name="description"></textarea>
          <button class="primary-btn" type="submit">创建项目</button>
        </form>

        <form id="taskForm" class="item">
          <h4>任务拆解</h4>
          <label>项目</label>
          <select name="project_id" required>${state.projects.map((p) => `<option value="${p.id}">${p.name}</option>`).join('')}</select>
          <label>任务描述</label><textarea name="description" required></textarea>
          <label>责任人</label><select name="assignee_id"><option value="">未分配</option>${employeeOptions}</select>
          <label>截止日期</label><input name="due_date" type="datetime-local" />
          <label>优先级</label><select name="priority"><option>low</option><option selected>medium</option><option>high</option></select>
          <label>状态</label><select name="status"><option selected>todo</option><option>in_progress</option><option>done</option></select>
          <button class="primary-btn" type="submit">创建任务</button>
        </form>
      </div>
      <div id="projectList" class="data-list"></div>
    `),
  );

  const listEl = document.getElementById('projectList');
  listEl.innerHTML = '';
  for (const project of state.projects) {
    let tasks = [];
    try {
      tasks = await api(`/projects/${project.id}/tasks`);
    } catch {
      tasks = [];
    }
    const listView = tasks
      .map((task) => `<div class="item">${task.description} <span class="tag">${task.status}</span><div class="small">责任人：${task.assignee_display || '未分配'}</div><button class="secondary-btn run-task-btn" data-task-id="${task.id}">AI执行规划</button></div>`)
      .join('');

    listEl.appendChild(
      card(`<h4>${project.name}</h4><div class="small">目标：${project.objective || '未填写'} | 负责人：${project.lead_display || '未分配'}</div>
      <p class="small">列表视图</p>${listView || '<div class="small">暂无任务</div>'}
      <p class="small">看板视图</p>${renderTasksKanban(tasks)}`),
    );
  }

  listEl.querySelectorAll('.run-task-btn').forEach((btn) => {
    btn.onclick = async () => {
      try {
        const result = await api(`/projects/tasks/${btn.dataset.taskId}/execute`, 'POST', {});
        setStatus(`任务 #${result.task_id} 已生成执行计划`);
      } catch (err) {
        setStatus(err.message, true);
      }
    };
  });

  document.getElementById('projectForm').onsubmit = async (e) => {
    e.preventDefault();
    const payload = Object.fromEntries(new FormData(e.target).entries());
    payload.company_id = state.companyId;
    try {
      await api('/projects', 'POST', payload);
      setStatus('项目创建成功');
      await renderProjects();
    } catch (err) {
      setStatus(err.message, true);
    }
  };

  document.getElementById('taskForm').onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const projectId = fd.get('project_id');
    const payload = Object.fromEntries(fd.entries());
    delete payload.project_id;
    try {
      await api(`/projects/${projectId}/tasks`, 'POST', payload);
      setStatus('任务创建成功');
      await renderProjects();
    } catch (err) {
      setStatus(err.message, true);
    }
  };
}

async function renderFinance() {
  const el = document.getElementById('view-finance');
  el.innerHTML = '';
  if (!state.companyId) {
    el.appendChild(card(`<h3>${t('noCompany')}</h3>`));
    return;
  }
  let dashboard = { tokens_used: 0, ai_cost: 0, income: 0, expense: 0, profit: 0 };
  try {
    dashboard = await api(`/finance/dashboard?company_id=${state.companyId}`);
  } catch (err) {
    setStatus(err.message, true);
  }

  const warnClass = dashboard.ai_cost > dashboard.income * 0.6 ? 'warn' : '';
  const profitClass = dashboard.profit < 0 ? 'danger' : '';

  el.appendChild(
    card(`
      <h3>财务驾驶舱（含 AI 成本）</h3>
      <div class="small">上次更新时间：${new Date().toLocaleString()}</div>
      <div class="grid">
        <div class="item kpi"><span>AI 调用 Token</span><strong>${dashboard.tokens_used}</strong></div>
        <div class="item kpi ${warnClass}"><span>AI 成本</span><strong>${dashboard.ai_cost.toFixed(2)}</strong></div>
        <div class="item kpi"><span>收入</span><strong>${dashboard.income.toFixed(2)}</strong></div>
        <div class="item kpi"><span>支出</span><strong>${dashboard.expense.toFixed(2)}</strong></div>
        <div class="item kpi ${profitClass}"><span>利润</span><strong>${dashboard.profit.toFixed(2)}</strong></div>
      </div>
      <p class="small">异常高亮：AI 成本超过收入 60% 或利润为负。</p>
      <div class="grid">
        <form id="tokenUsageForm" class="item">
          <h4>新增 AI Token 用量</h4>
          <label>模型</label><input name="model" required />
          <label>Token 数</label><input name="tokens_used" type="number" required />
          <label>成本</label><input name="cost" type="number" step="0.0001" required />
          <button class="primary-btn">提交</button>
        </form>
        <form id="recordForm" class="item">
          <h4>新增财务流水</h4>
          <label>描述</label><input name="description" required />
          <label>金额</label><input name="amount" type="number" step="0.01" required />
          <label>类型</label><select name="record_type"><option value="income">income</option><option value="expense">expense</option></select>
          <button class="primary-btn">提交</button>
        </form>
      </div>
    `),
  );

  document.getElementById('tokenUsageForm').onsubmit = async (e) => {
    e.preventDefault();
    const payload = Object.fromEntries(new FormData(e.target).entries());
    payload.company_id = state.companyId;
    try {
      await api('/finance/token-usage', 'POST', payload);
      setStatus('Token 用量已记录');
      await renderFinance();
    } catch (err) {
      setStatus(err.message, true);
    }
  };

  document.getElementById('recordForm').onsubmit = async (e) => {
    e.preventDefault();
    const payload = Object.fromEntries(new FormData(e.target).entries());
    payload.company_id = state.companyId;
    try {
      await api('/finance/records', 'POST', payload);
      setStatus('财务流水已记录');
      await renderFinance();
    } catch (err) {
      setStatus(err.message, true);
    }
  };
}

async function renderTools() {
  const el = document.getElementById('view-tools');
  el.innerHTML = '';
  if (!state.companyId) {
    el.appendChild(card(`<h3>${t('noCompany')}</h3>`));
    return;
  }

  const toolExamples = [
    {
      id: 'web_search',
      name: '网页搜索（SERP）',
      category: '信息检索',
      integration_mode: 'API',
      auth_type: 'API Key',
      description: '用于联网检索最新资讯、政策、竞品与事实核查。',
      responsibility_scope: '当任务需要外部事实时，先检索再回答，并给出来源摘要。',
      config: { base_url: 'https://api.search.example/v1', endpoint: '/search', timeout_ms: 15000 },
    },
    {
      id: 'web_scraper',
      name: '网页抓取（Crawler）',
      category: '数据采集',
      integration_mode: 'MCP',
      auth_type: '无需认证',
      description: '抓取指定网页正文、标题与结构化字段，支持批量链接。',
      responsibility_scope: '只抓取用户授权站点，输出可追溯数据。',
      config: { allow_domains: ['example.com'], max_pages: 50, extract_mode: 'article' },
    },
    {
      id: 'knowledge_base',
      name: '企业知识库检索',
      category: '知识库',
      integration_mode: 'MCP',
      auth_type: 'Token',
      description: '向量检索企业制度、SOP 与历史案例。',
      responsibility_scope: '优先返回企业内部知识，找不到再建议外部查询。',
      config: { index_name: 'company_kb', top_k: 5, rerank: true },
    },
    {
      id: 'sql_report',
      name: 'SQL 报表工具',
      category: '数据分析',
      integration_mode: 'API',
      auth_type: 'OAuth2',
      description: '执行白名单 SQL 模板，输出业务报表。',
      responsibility_scope: '仅使用预设模板与参数，禁止任意 SQL。',
      config: { datasource: 'finance_dw', allowed_templates: ['daily_revenue', 'cost_breakdown'] },
    },
    {
      id: 'sheet_sync',
      name: '表格同步工具',
      category: '协作办公',
      integration_mode: 'API',
      auth_type: 'OAuth2',
      description: '同步在线表格，适合运营台账回写与共享。',
      responsibility_scope: '写入前先校验字段映射和去重键。',
      config: { provider: 'google_sheets', spreadsheet_id: 'demo_sheet_id' },
    },
    {
      id: 'mail_sender',
      name: '邮件发送',
      category: '沟通通知',
      integration_mode: 'API',
      auth_type: 'API Key',
      description: '发送通知、审批结果和客户触达邮件。',
      responsibility_scope: '仅可发送模板邮件并记录发送日志。',
      config: { sender: 'noreply@signx.local', template_mode: true },
    },
    {
      id: 'im_bot',
      name: 'IM 机器人（飞书/钉钉/Slack）',
      category: '沟通通知',
      integration_mode: 'Webhook',
      auth_type: 'Token',
      description: '推送告警、日报与流程状态更新。',
      responsibility_scope: '只发工作群，消息带来源与负责人。',
      config: { webhook_url: 'https://hooks.example.com/bot/xxx', mention_policy: 'owner_on_error' },
    },
    {
      id: 'ocr_parser',
      name: 'OCR 文档解析',
      category: '文档处理',
      integration_mode: 'API',
      auth_type: 'API Key',
      description: '识别发票、合同、回单并结构化字段。',
      responsibility_scope: '返回识别置信度，低置信字段要求人工复核。',
      config: { language: 'zh-CN', doc_types: ['invoice', 'contract'] },
    },
    {
      id: 'calendar_scheduler',
      name: '日程排班',
      category: '协作办公',
      integration_mode: 'API',
      auth_type: 'OAuth2',
      description: '创建会议、排班和截止提醒。',
      responsibility_scope: '冲突时优先给出候选时间，不直接覆盖。',
      config: { timezone: 'Asia/Shanghai', default_duration_min: 30 },
    },
    {
      id: 'workflow_engine',
      name: '流程引擎（审批/工单）',
      category: '流程自动化',
      integration_mode: 'MCP',
      auth_type: 'Token',
      description: '触发审批流、工单流和跨系统自动化流程。',
      responsibility_scope: '关键节点必须记录审计轨迹，支持回滚。',
      config: { process_keys: ['expense_approval', 'it_ticket'], audit_required: true },
    },
  ];

  let tools = [];
  try {
    tools = await api(`/tools?company_id=${state.companyId}`);
  } catch (err) {
    setStatus(err.message, true);
  }

  el.appendChild(
    card(`
      <h3>工具中心与自动化</h3>
      <div class="guide-steps">
        <div class="step"><strong>1. 选样例或手动填写</strong><span>先选择常用样例可快速生成配置。</span></div>
        <div class="step"><strong>2. 定义职责范围</strong><span>输入工具职责，系统会生成可复用 AI Prompt。</span></div>
        <div class="step"><strong>3. 验证并保存</strong><span>保存后可在下方编辑，并用于 Openclaw 调度。</span></div>
      </div>
      <div class="grid">
        <form id="toolForm" class="item">
          <h4>工具注册与配置（支持编辑）</h4>
          <label>快捷样例（10种常用工具）</label>
          <select id="toolTemplatePicker">
            <option value="">手动填写</option>
            ${toolExamples.map((tool) => `<option value="${tool.id}">${tool.name}</option>`).join('')}
          </select>
          <label>工具名称</label><input name="name" required />
          <label>工具分类</label>
          <select name="category">
            <option value="信息检索">信息检索</option>
            <option value="数据采集">数据采集</option>
            <option value="知识库">知识库</option>
            <option value="数据分析">数据分析</option>
            <option value="协作办公">协作办公</option>
            <option value="沟通通知">沟通通知</option>
            <option value="文档处理">文档处理</option>
            <option value="流程自动化">流程自动化</option>
            <option value="其他">其他</option>
          </select>
          <label>接入模式</label>
          <select name="integration_mode">
            <option value="MCP">MCP</option>
            <option value="API" selected>API</option>
            <option value="Webhook">Webhook</option>
            <option value="SDK">SDK</option>
          </select>
          <label>认证方式</label>
          <select name="auth_type">
            <option value="API Key" selected>API Key</option>
            <option value="OAuth2">OAuth2</option>
            <option value="Token">Token</option>
            <option value="无需认证">无需认证</option>
          </select>
          <label>描述</label><textarea name="description"></textarea>
          <label>职责边界（用于生成 Prompt）</label><textarea name="responsibility_scope" placeholder="例如：仅做财务报表汇总，不做会计分录修改。"></textarea>
          <div class="inline-actions">
            <button id="generatePromptBtn" type="button" class="secondary-btn">生成 AI Prompt</button>
            <button id="clearEditBtn" type="button" class="ghost-btn">清空编辑状态</button>
          </div>
          <label>AI Prompt（可复用）</label><textarea name="ai_prompt" id="aiPromptField" placeholder="点击“生成 AI Prompt”后自动填充"></textarea>
          <label>配置（JSON）</label><textarea name="config" id="toolConfigField">{"base_url":""}</textarea>
          <label><input type="checkbox" name="supported_by_mcp" /> 支持 MCP 标准接入</label>
          <input type="hidden" name="editing_tool_id" />
          <button class="primary-btn" type="submit">保存工具</button>
        </form>
        <form id="openclawForm" class="item">
          <h4>Openclaw 自动化执行</h4>
          <label>任务名</label><input name="task_name" required />
          <label>执行载荷（JSON）</label><textarea name="payload">{"run":"demo"}</textarea>
          <button class="secondary-btn" type="submit">提交执行</button>
        </form>
      </div>
      <h4>工具清单（可编辑）</h4>
      <div id="toolList" class="data-list"></div>
    `),
  );

  const toolForm = document.getElementById('toolForm');
  const toolTemplatePicker = document.getElementById('toolTemplatePicker');
  const toolListEl = document.getElementById('toolList');
  const clearEditBtn = document.getElementById('clearEditBtn');
  const generatePromptBtn = document.getElementById('generatePromptBtn');

  const buildPrompt = (payload) => {
    const responsibilities = payload.responsibility_scope || '按照用户输入执行并保持结果可追溯';
    return [
      `你是 ${payload.name || '企业工具'} 的调度代理。`,
      `工具分类：${payload.category || '其他'}；接入模式：${payload.integration_mode || 'API'}；认证方式：${payload.auth_type || 'API Key'}。`,
      `职责边界：${responsibilities}。`,
      '执行规范：先校验输入参数，再调用工具；输出包含关键结果、异常信息、下一步建议。',
      '安全要求：不得泄露密钥，不执行越权操作，保留审计字段（操作者、时间、参数摘要）。',
    ].join('\n');
  };

  const resetToolForm = () => {
    toolForm.reset();
    toolForm.elements.config.value = '{"base_url":""}';
    toolForm.elements.editing_tool_id.value = '';
    toolTemplatePicker.value = '';
    document.querySelector('#toolForm button[type="submit"]').textContent = '保存工具';
  };

  toolTemplatePicker.onchange = () => {
    const picked = toolExamples.find((tool) => tool.id === toolTemplatePicker.value);
    if (!picked) {
      return;
    }
    toolForm.elements.name.value = picked.name;
    toolForm.elements.category.value = picked.category;
    toolForm.elements.integration_mode.value = picked.integration_mode;
    toolForm.elements.auth_type.value = picked.auth_type;
    toolForm.elements.description.value = picked.description;
    toolForm.elements.responsibility_scope.value = picked.responsibility_scope;
    toolForm.elements.supported_by_mcp.checked = picked.integration_mode === 'MCP';
    toolForm.elements.ai_prompt.value = buildPrompt(picked);
    toolForm.elements.config.value = JSON.stringify(picked.config, null, 2);
    setStatus(`已加载样例：${picked.name}`);
  };

  toolListEl.innerHTML = tools
    .map((tool) => {
      const config = tool.config || {};
      return `<div class="item">
        <div class="inline-actions">
          <strong>${tool.name}</strong>
          <span class="tag">${config.category || '未分类'}</span>
          <span class="tag">${tool.supported_by_mcp ? 'MCP' : config.integration_mode || 'custom'}</span>
          <button class="secondary-btn edit-tool-btn" data-id="${tool.id}">编辑</button>
        </div>
        <div class="small">${tool.description || '暂无描述'}</div>
        <div class="small">职责：${config.responsibility_scope || '未定义'} </div>
        <details>
          <summary>查看配置与Prompt</summary>
          <pre>${JSON.stringify(config, null, 2)}</pre>
          <pre>${config.ai_prompt || '暂无 AI Prompt'}</pre>
        </details>
      </div>`;
    })
    .join('');

  toolListEl.querySelectorAll('.edit-tool-btn').forEach((btn) => {
    btn.onclick = () => {
      const current = tools.find((tool) => tool.id === Number(btn.dataset.id));
      if (!current) {
        return;
      }
      const config = current.config || {};
      toolForm.elements.name.value = current.name || '';
      toolForm.elements.description.value = current.description || '';
      toolForm.elements.category.value = config.category || '其他';
      toolForm.elements.integration_mode.value = config.integration_mode || (current.supported_by_mcp ? 'MCP' : 'API');
      toolForm.elements.auth_type.value = config.auth_type || 'API Key';
      toolForm.elements.responsibility_scope.value = config.responsibility_scope || '';
      toolForm.elements.ai_prompt.value = config.ai_prompt || '';
      toolForm.elements.config.value = JSON.stringify(config, null, 2);
      toolForm.elements.supported_by_mcp.checked = Boolean(current.supported_by_mcp);
      toolForm.elements.editing_tool_id.value = current.id;
      toolTemplatePicker.value = '';
      document.querySelector('#toolForm button[type="submit"]').textContent = `更新工具 #${current.id}`;
      toolForm.scrollIntoView({ behavior: 'smooth', block: 'start' });
      setStatus(`正在编辑：${current.name}`);
    };
  });

  generatePromptBtn.onclick = () => {
    const payload = Object.fromEntries(new FormData(toolForm).entries());
    toolForm.elements.ai_prompt.value = buildPrompt(payload);
    setStatus('已生成 AI Prompt，可继续修改后保存。');
  };

  clearEditBtn.onclick = () => {
    resetToolForm();
    setStatus('已清空编辑状态');
  };

  toolForm.onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const payload = Object.fromEntries(fd.entries());
    payload.company_id = state.companyId;
    payload.supported_by_mcp = Boolean(fd.get('supported_by_mcp'));

    let config = {};
    try {
      config = JSON.parse(payload.config || '{}');
    } catch {
      setStatus('配置 JSON 格式错误', true);
      return;
    }

    config.category = payload.category;
    config.integration_mode = payload.integration_mode;
    config.auth_type = payload.auth_type;
    config.responsibility_scope = payload.responsibility_scope;
    config.ai_prompt = payload.ai_prompt || buildPrompt(payload);
    payload.config = config;

    delete payload.category;
    delete payload.integration_mode;
    delete payload.auth_type;
    delete payload.responsibility_scope;
    delete payload.ai_prompt;

    const editingId = payload.editing_tool_id;
    delete payload.editing_tool_id;

    try {
      if (editingId) {
        await api(`/tools/${editingId}`, 'PUT', payload);
        setStatus(`工具 #${editingId} 更新成功`);
      } else {
        await api('/tools', 'POST', payload);
        setStatus('工具注册成功');
      }
      await renderTools();
    } catch (err) {
      setStatus(err.message, true);
    }
  };

  document.getElementById('openclawForm').onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const payload = Object.fromEntries(fd.entries());
    payload.company_id = state.companyId;
    try {
      payload.payload = JSON.parse(payload.payload || '{}');
    } catch {
      setStatus('Payload JSON 格式错误', true);
      return;
    }

    try {
      const result = await api('/tools/openclaw/execute', 'POST', payload);
      setStatus(`自动化任务已提交：${result.task_name} (${result.status})`);
    } catch (err) {
      setStatus(err.message, true);
    }
  };
}


async function renderAdmin() {
  const el = document.getElementById('view-admin');
  el.innerHTML = '';
  if (!state.me) {
    el.appendChild(card(`<h3>${t('pleaseLogin')}</h3>`));
    return;
  }

  el.appendChild(card('<h3>平台管理员：租户审核 / 全局统计 / 权限巡检</h3><div id="adminContent" class="small">加载中...</div>'));

  try {
    const [tenants, users, audits, aiSettings] = await Promise.all([api('/admin/tenants'), api('/admin/users'), api('/admin/audits'), api('/admin/settings/ai-model')]);
    document.getElementById('adminContent').innerHTML = `
      <div class="grid">
        <div class="item"><h4>租户列表 (${tenants.length})</h4>${tenants.map((t) => `<div>${t.id}. ${t.name}</div>`).join('')}</div>
        <div class="item"><h4>用户列表 (${users.length})</h4>${users.map((u) => `<div>${u.email} - ${u.platform_role}</div>`).join('')}</div>
        <div class="item"><h4>审计日志 (最近 ${audits.length})</h4>${audits.slice(0, 10).map((a) => `<div>${a.created_at}: ${a.action}</div>`).join('')}</div>
      </div>
      <form id="aiModelSettingForm" class="item">
        <h4>系统设置：全局 AI 模型 API</h4>
        <label>预置模型</label><select name="preset_id" required>${(aiSettings.presets || []).map((preset) => `<option value="${preset.id}" ${aiSettings.current?.preset_id === preset.id ? 'selected' : ''}>${preset.label} | ${preset.base_url} | ${preset.model}</option>`).join('')}</select>
        <div class="small">接口地址/模型类型/模型名由预置自动带出，仅需填写或更新 API Key。</div>
        <label>API Key</label><input name="api_key" type="password" placeholder="${aiSettings.current?.api_key ? '已配置，留空不修改' : '请输入Key'}" />
        <button class="primary-btn" type="submit">保存系统AI配置</button>
      </form>
    `;

    document.getElementById('aiModelSettingForm').onsubmit = async (e) => {
      e.preventDefault();
      const payload = Object.fromEntries(new FormData(e.target).entries());
      try {
        await api('/admin/settings/ai-model', 'PUT', payload);
        setStatus('系统AI模型配置已保存');
        await renderAdmin();
      } catch (err) {
        setStatus(err.message, true);
      }
    };
  } catch (err) {
    document.getElementById('adminContent').textContent = `无权限或加载失败：${err.message}`;
  }
}

async function renderCurrentView() {
  if (state.activeView === 'auth') return renderAuth();
  if (state.activeView === 'companies') return renderCompanies();
  if (state.activeView === 'employees') return renderEmployees();
  if (state.activeView === 'projects') return renderProjects();
  if (state.activeView === 'finance') return renderFinance();
  if (state.activeView === 'tools') return renderTools();
  if (state.activeView === 'admin') return renderAdmin();
}

async function renderAll() {
  renderNav();
  switchView();
  await renderCurrentView();
}

document.getElementById('refreshBtn').onclick = async () => {
  await renderCurrentView();
  setStatus('当前模块已刷新');
};

document.getElementById('langBtn').onclick = () => {
  state.lang = state.lang === 'zh' ? 'en' : 'zh';
  document.getElementById('langBtn').textContent = state.lang === 'zh' ? 'EN' : '中文';
  renderAll();
};

document.getElementById('logoutBtn').onclick = async () => {
  if (!state.me) {
    setStatus(t('pleaseLogin'), true);
    return;
  }
  try {
    await api('/auth/logout', 'POST');
    state.me = null;
    state.companyId = null;
    state.activeView = 'auth';
    setStatus('已退出登录');
    await renderAll();
  } catch (err) {
    setStatus(err.message, true);
  }
};

(async function bootstrap() {
  try {
    state.me = await api('/auth/me');
    state.companyId = state.me.company_id || null;
    state.activeView = 'companies';
    setStatus(`${t('loggedIn')}${state.me.email}`);
  } catch {
    setStatus(t('pleaseLogin'));
    state.activeView = 'auth';
  }
  renderAll();
})();

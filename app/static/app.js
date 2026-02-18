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
          <label>组织结构说明</label><textarea name="organization_structure"></textarea>
          <p class="small">提示：未分配岗位建议后续在员工管理中补齐。</p>
          <button class="primary-btn" type="submit">创建企业</button>
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
      </div>`,
    )
    .join('');

  listEl.querySelectorAll('.pick-company').forEach((btn) => {
    btn.onclick = () => {
      state.companyId = Number(btn.dataset.company);
      setStatus(`已切换当前企业：${state.companyId}`);
    };
  });

  document.getElementById('companyForm').onsubmit = async (e) => {
    e.preventDefault();
    const payload = Object.fromEntries(new FormData(e.target).entries());
    try {
      const company = await api('/companies', 'POST', payload);
      state.companyId = company.id;
      setStatus(`企业创建成功：${company.name}`);
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
  try {
    employees = await api(`/employees?company_id=${state.companyId}`);
  } catch (err) {
    setStatus(err.message, true);
  }

  el.appendChild(
    card(`
      <h3>员工与角色管理</h3>
      <form id="employeeForm" class="grid">
        <div class="item">
          <label>姓名</label><input name="name" required />
          <label>岗位职责</label><textarea name="primary_tasks"></textarea>
          <label>公司角色</label>
          <select name="company_role">
            <option value="owner">owner</option>
            <option value="finance_manager">finance_manager</option>
            <option value="hr_manager">hr_manager</option>
            <option value="project_lead">project_lead</option>
            <option value="member" selected>member</option>
          </select>
        </div>
        <div class="item">
          <label>AI 服务商</label>
          <select name="ai_provider">
            <option value="">未设置</option>
            <option>OpenAI</option><option>Gemini</option><option>Claude</option><option>DeepSeek</option><option>Kimi</option><option>ChatGLM</option><option>Custom</option>
          </select>
          <details>
            <summary>高级配置（折叠）</summary>
            <label>API Key（敏感）</label><input name="api_key_encrypted" type="password" />
            <div class="small">显示将脱敏为 *** ，提交前请确认。</div>
          </details>
          <button class="primary-btn" type="submit">新增员工</button>
        </div>
      </form>
    `),
  );

  const list = card('<h3>员工列表</h3><div id="employeeList" class="data-list"></div>');
  list.querySelector('#employeeList').innerHTML = employees
    .map(
      (e) => `<div class="item"><strong>${e.name}</strong> <span class="tag">${e.company_role}</span>
      <div class="small">职责：${e.primary_tasks || '未填写'}</div>
      <div class="small">AI：${e.ai_provider || '未配置'} | Key：${e.api_key_masked || '空'}</div></div>`,
    )
    .join('');
  el.appendChild(list);

  document.getElementById('employeeForm').onsubmit = async (evt) => {
    evt.preventDefault();
    const payload = Object.fromEntries(new FormData(evt.target).entries());
    payload.company_id = state.companyId;
    if (payload.api_key_encrypted && !window.confirm('即将保存敏感 API Key，是否确认？')) {
      return;
    }
    try {
      await api('/employees', 'POST', payload);
      setStatus('员工创建成功');
      await renderEmployees();
    } catch (err) {
      setStatus(err.message, true);
    }
  };
}

function renderTasksKanban(tasks) {
  const columns = {
    todo: [],
    in_progress: [],
    done: [],
  };
  tasks.forEach((t) => {
    if (columns[t.status]) {
      columns[t.status].push(t);
    }
  });
  return `<div class="kanban">${Object.entries(columns)
    .map(
      ([k, list]) => `<div class="kanban-col"><h4>${k}</h4>${list
        .map(
          (task) => `<div class="item"><strong>${task.description}</strong><div class="small">优先级：${task.priority} | 截止：${task.due_date || '无'}</div></div>`,
        )
        .join('')}</div>`,
    )
    .join('')}</div>`;
}

async function renderProjects() {
  const el = document.getElementById('view-projects');
  el.innerHTML = '';
  if (!state.companyId) {
    el.appendChild(card(`<h3>${t('noCompany')}</h3>`));
    return;
  }

  try {
    state.projects = await api(`/projects?company_id=${state.companyId}`);
  } catch (err) {
    setStatus(err.message, true);
    return;
  }

  el.appendChild(
    card(`
      <h3>项目与任务协同</h3>
      <div class="grid">
        <form id="projectForm" class="item">
          <h4>创建项目</h4>
          <label>项目名称</label><input name="name" required />
          <label>项目目标</label><textarea name="objective"></textarea>
          <label>负责人 employee_id</label><input name="lead_id" type="number" />
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
          <label>责任人 assignee_id</label><input name="assignee_id" type="number" />
          <label>截止日期</label><input name="due_date" type="datetime-local" />
          <label>优先级</label>
          <select name="priority"><option>low</option><option selected>medium</option><option>high</option></select>
          <label>状态</label>
          <select name="status"><option selected>todo</option><option>in_progress</option><option>done</option></select>
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
      .map((task) => `<div class="item">${task.description} <span class="tag">${task.status}</span> <div class="small">依赖任务: ${task.dependency_task_id || '无'}</div></div>`)
      .join('');

    listEl.appendChild(
      card(`<h4>${project.name}</h4><div class="small">目标：${project.objective || '未填写'} | 负责人：${project.lead_id || '未分配'}</div>
      <p class="small">列表视图</p>${listView || '<div class="small">暂无任务</div>'}
      <p class="small">看板视图</p>${renderTasksKanban(tasks)}`),
    );
  }

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

  let tools = [];
  try {
    tools = await api(`/tools?company_id=${state.companyId}`);
  } catch (err) {
    setStatus(err.message, true);
  }

  el.appendChild(
    card(`
      <h3>工具中心与自动化</h3>
      <div class="grid">
        <form id="toolForm" class="item">
          <h4>工具注册与配置（MCP）</h4>
          <label>工具名称</label><input name="name" required />
          <label>描述</label><textarea name="description"></textarea>
          <label>配置（JSON）</label><textarea name="config">{"base_url":""}</textarea>
          <label><input type="checkbox" name="supported_by_mcp" /> 支持 MCP 标准接入</label>
          <button class="primary-btn">注册工具</button>
        </form>
        <form id="openclawForm" class="item">
          <h4>Openclaw 自动化执行</h4>
          <label>任务名</label><input name="task_name" required />
          <label>执行载荷（JSON）</label><textarea name="payload">{"run":"demo"}</textarea>
          <button class="secondary-btn">提交执行</button>
        </form>
      </div>
      <h4>工具清单</h4>
      <div id="toolList" class="data-list"></div>
    `),
  );

  document.getElementById('toolList').innerHTML = tools
    .map((tool) => `<div class="item"><strong>${tool.name}</strong> <span class="tag">${tool.supported_by_mcp ? 'MCP' : 'custom'}</span><div class="small">${tool.description || ''}</div><pre>${JSON.stringify(tool.config, null, 2)}</pre></div>`)
    .join('');

  document.getElementById('toolForm').onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const payload = Object.fromEntries(fd.entries());
    payload.company_id = state.companyId;
    payload.supported_by_mcp = Boolean(fd.get('supported_by_mcp'));
    try {
      payload.config = JSON.parse(payload.config || '{}');
    } catch {
      setStatus('配置 JSON 格式错误', true);
      return;
    }

    try {
      await api('/tools', 'POST', payload);
      setStatus('工具注册成功');
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
    const [tenants, users, audits] = await Promise.all([api('/admin/tenants'), api('/admin/users'), api('/admin/audits')]);
    document.getElementById('adminContent').innerHTML = `
      <div class="grid">
        <div class="item"><h4>租户列表 (${tenants.length})</h4>${tenants
          .map((t) => `<div>${t.id}. ${t.name}</div>`)
          .join('')}</div>
        <div class="item"><h4>用户列表 (${users.length})</h4>${users
          .map((u) => `<div>${u.email} - ${u.platform_role}</div>`)
          .join('')}</div>
        <div class="item"><h4>审计日志 (最近 ${audits.length})</h4>${audits
          .slice(0, 10)
          .map((a) => `<div>${a.created_at}: ${a.action}</div>`)
          .join('')}</div>
      </div>
    `;
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

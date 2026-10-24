/* ===================================================================
   UniBudget - Student Budget Tracker Core Application Logic
   =================================================================== */

(function () {
  'use strict';

  // State
  let token = localStorage.getItem('sbt_token') || null;
  let currentUser = null;
  let currentSummary = null;
  let currentMonth = new Date().toISOString().slice(0, 7); // 'YYYY-MM'
  let cachedExpenses = [];
  let cachedCategories = [];

  // DOM Elements
  const authSection = document.getElementById('authSection');
  const dashboardSection = document.getElementById('dashboardSection');
  const navUserMenu = document.getElementById('navUserMenu');
  const navMonthContainer = document.getElementById('navMonthContainer');
  const selectedMonthInput = document.getElementById('selectedMonth');
  const navUserName = document.getElementById('navUserName');
  const navUserSchool = document.getElementById('navUserSchool');
  const navUserAvatar = document.getElementById('navUserAvatar');
  const themeToggleBtn = document.getElementById('themeToggleBtn');
  const themeIcon = document.getElementById('themeIcon');

  // Modals
  const expenseModal = document.getElementById('expenseModal');
  const categoryModal = document.getElementById('categoryModal');
  const affordabilityModal = document.getElementById('affordabilityModal');
  const profileModal = document.getElementById('profileModal');

  // Forms
  const loginForm = document.getElementById('loginForm');
  const registerForm = document.getElementById('registerForm');
  const expenseForm = document.getElementById('expenseForm');
  const categoryForm = document.getElementById('categoryForm');
  const affordabilityForm = document.getElementById('affordabilityForm');
  const profileForm = document.getElementById('profileForm');

  // API Client Helper
  async function apiCall(endpoint, options = {}) {
    options.headers = options.headers || {};
    if (token) {
      options.headers['Authorization'] = `Bearer ${token}`;
    }
    if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
      options.headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(options.body);
    }

    try {
      const res = await fetch(endpoint, options);
      if (res.status === 401) {
        logout(false);
        showToast('Session expired. Please log in again.', 'error');
        return null;
      }
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Request failed');
      }
      return data;
    } catch (err) {
      showToast(err.message, 'error');
      return null;
    }
  }

  // Toast System
  function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '⚠️';

    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  // Theme Management
  function initTheme() {
    const saved = localStorage.getItem('sbt_theme') || 'light';
    setTheme(saved);
  }

  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('sbt_theme', theme);
    if (themeIcon) {
      themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
    }
    if (currentSummary && window.AppCharts) {
      window.AppCharts.updateAll(currentSummary);
    }
  }

  function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    setTheme(current === 'dark' ? 'light' : 'dark');
  }

  // Auth Handling
  async function initAuth() {
    selectedMonthInput.value = currentMonth;

    if (!token) {
      showAuth();
      return;
    }

    const res = await apiCall('/api/auth/me');
    if (res && res.user) {
      currentUser = res.user;
      showDashboard();
    } else {
      showAuth();
    }
  }

  function showAuth() {
    authSection.style.display = 'flex';
    dashboardSection.style.display = 'none';
    navUserMenu.style.display = 'none';
    navMonthContainer.style.display = 'none';
  }

  function showDashboard() {
    authSection.style.display = 'none';
    dashboardSection.style.display = 'block';
    navUserMenu.style.display = 'flex';
    navMonthContainer.style.display = 'flex';

    updateNavUser();
    loadDashboard();
  }

  function updateNavUser() {
    if (!currentUser) return;
    navUserName.textContent = currentUser.name;
    navUserSchool.textContent = `${currentUser.university} (${currentUser.major || 'Student'})`;

    const initials = currentUser.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    navUserAvatar.textContent = initials || 'ST';
  }

  async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value.trim();

    const data = await apiCall('/api/auth/login', {
      method: 'POST',
      body: { email, password }
    });

    if (data && data.token) {
      token = data.token;
      currentUser = data.user;
      localStorage.setItem('sbt_token', token);
      showToast(`Welcome back, ${currentUser.name}!`, 'success');
      showDashboard();
    }
  }

  async function handleRegister(e) {
    e.preventDefault();
    const payload = {
      name: document.getElementById('regName').value.trim(),
      email: document.getElementById('regEmail').value.trim(),
      password: document.getElementById('regPassword').value.trim(),
      university: document.getElementById('regUniversity').value.trim() || 'State University',
      major: document.getElementById('regMajor').value.trim() || 'General Studies',
      monthly_budget: parseFloat(document.getElementById('regBudget').value) || 1200,
      currency: document.getElementById('regCurrency').value || '$',
      hourly_wage: 15.0
    };

    const data = await apiCall('/api/auth/register', {
      method: 'POST',
      body: payload
    });

    if (data && data.token) {
      token = data.token;
      currentUser = data.user;
      localStorage.setItem('sbt_token', token);
      showToast('Account created successfully!', 'success');
      showDashboard();
    }
  }

  async function handleDemoLogin() {
    const data = await apiCall('/api/auth/demo-login', { method: 'POST' });
    if (data && data.token) {
      token = data.token;
      currentUser = data.user;
      localStorage.setItem('sbt_token', token);
      showToast('Logged in as Demo Student Alex Rivers!', 'success');
      showDashboard();
    }
  }

  async function logout(notify = true) {
    if (token) {
      await apiCall('/api/auth/logout', { method: 'POST' });
    }
    token = null;
    currentUser = null;
    currentSummary = null;
    localStorage.removeItem('sbt_token');
    showAuth();
    if (notify) showToast('Logged out successfully.', 'info');
  }

  // Dashboard Data Loading
  async function loadDashboard() {
    currentMonth = selectedMonthInput.value || new Date().toISOString().slice(0, 7);
    const summary = await apiCall(`/api/summary?month=${currentMonth}`);
    if (!summary) return;

    currentSummary = summary;
    renderStatusBanner(summary);
    renderMetrics(summary);
    renderCategories(summary.categories || []);

    if (window.AppCharts) {
      window.AppCharts.updateAll(summary);
    }

    loadExpenses();
  }

  // Render Status Banner
  function renderStatusBanner(summary) {
    const banner = document.getElementById('statusBanner');
    const icon = document.getElementById('statusIcon');
    const heading = document.getElementById('statusHeading');
    const desc = document.getElementById('statusDescription');

    banner.style.setProperty('--banner-accent', summary.health_color);

    const curr = summary.currency;
    const daysLeft = summary.days_left;
    const safeDaily = summary.safe_daily_spend.toFixed(2);
    const spentPct = summary.percent_used.toFixed(0);

    if (summary.pacing_status === 'exceeded') {
      icon.textContent = '🚨';
      heading.textContent = `Budget Alert: Exceeded by ${curr}${Math.abs(summary.remaining_budget).toFixed(2)}`;
      desc.textContent = `You have spent ${spentPct}% of your budget with ${daysLeft} days left. Halt non-essential spending.`;
    } else if (summary.pacing_status === 'danger') {
      icon.textContent = '⚠️';
      heading.textContent = `Warning: Spending Ahead of Schedule (${spentPct}% used)`;
      desc.textContent = `Safe daily ceiling: ${curr}${safeDaily}/day for the remaining ${daysLeft} days.`;
    } else if (summary.pacing_status === 'caution') {
      icon.textContent = '⚖️';
      heading.textContent = `Pacing Notice: Spend Cautiously (${spentPct}% used)`;
      desc.textContent = `Safe daily allowance is ${curr}${safeDaily}/day for ${daysLeft} more days this month.`;
    } else {
      icon.textContent = '🛡️';
      heading.textContent = `Pacing Healthy: Great College Financial Discipline!`;
      desc.textContent = `You have spent ${curr}${summary.total_spent.toFixed(2)} (${spentPct}%). Safe allowance is ${curr}${safeDaily}/day for ${daysLeft} days.`;
    }
  }

  // Render Metrics
  function renderMetrics(summary) {
    const curr = summary.currency;

    document.getElementById('cardMonthlyBudget').textContent = `${curr}${summary.monthly_budget.toFixed(2)}`;
    document.getElementById('cardSpentPercent').textContent = `${summary.percent_used.toFixed(1)}% utilized`;
    document.getElementById('cardBudgetProgress').style.width = `${Math.min(100, summary.percent_used)}%`;

    document.getElementById('cardTotalSpent').textContent = `${curr}${summary.total_spent.toFixed(2)}`;
    document.getElementById('cardTxCount').textContent = `${summary.expense_count} total expense(s)`;
    document.getElementById('cardAvgDaily').textContent = `Avg: ${curr}${summary.avg_daily_spent.toFixed(2)}/day`;

    const remCard = document.getElementById('cardRemainingBalance');
    remCard.textContent = `${curr}${summary.remaining_budget.toFixed(2)}`;
    remCard.style.color = summary.remaining_budget < 0 ? 'var(--danger)' : 'var(--text-main)';

    const remBadge = document.getElementById('cardStatusBadge');
    remBadge.textContent = summary.health_label;
    remBadge.className = `badge badge-${summary.pacing_status === 'great' ? 'success' : (summary.pacing_status === 'exceeded' ? 'danger' : 'warning')}`;

    document.getElementById('cardDaysLeft').textContent = `${summary.days_left} day(s) left in month`;
    const remainingPct = Math.max(0, 100 - summary.percent_used);
    document.getElementById('cardRemainingProgressBar').style.width = `${remainingPct}%`;

    document.getElementById('cardSafeDaily').textContent = `${curr}${summary.safe_daily_spend.toFixed(2)}`;
    document.getElementById('chartCategoryCount').textContent = `${summary.categories.filter(c => c.spent > 0).length} Active`;
  }

  // Render Categories Grid
  function renderCategories(categories) {
    cachedCategories = categories;
    const grid = document.getElementById('categoriesGrid');
    const selectFilter = document.getElementById('txCategoryFilter');
    const modalSelect = document.getElementById('expCategory');

    grid.innerHTML = '';
    
    // Save current selection in filter
    const prevFilterVal = selectFilter.value;
    selectFilter.innerHTML = '<option value="">All Categories</option>';
    modalSelect.innerHTML = '';

    const curr = currentSummary ? currentSummary.currency : '$';

    categories.forEach(cat => {
      // Add to select dropdowns
      const opt1 = document.createElement('option');
      opt1.value = cat.id;
      opt1.textContent = `${cat.icon} ${cat.name}`;
      selectFilter.appendChild(opt1);

      const opt2 = document.createElement('option');
      opt2.value = cat.id;
      opt2.textContent = `${cat.icon} ${cat.name}`;
      modalSelect.appendChild(opt2);

      // Card element
      const card = document.createElement('div');
      card.className = 'category-card';

      const pct = Math.min(100, cat.percent_used);
      const isOver = cat.spent > cat.budget_limit;
      const barColor = isOver ? '#ef4444' : (pct > 80 ? '#f59e0b' : cat.color);

      card.innerHTML = `
        <div class="category-header">
          <div class="category-info">
            <div class="category-icon-bubble" style="background-color: ${cat.color}20; color: ${cat.color};">
              ${cat.icon}
            </div>
            <div>
              <div class="category-title">${cat.name}</div>
              <div style="font-size: 0.72rem; color: var(--text-muted);">${cat.tx_count || 0} transaction(s)</div>
            </div>
          </div>
          <button class="btn-icon-sm edit-cat-btn" data-id="${cat.id}" title="Edit Cap">✏️</button>
        </div>
        <div class="category-spending">
          <div>
            <span class="category-spent-val" style="color: ${isOver ? 'var(--danger)' : 'var(--text-main)'};">
              ${curr}${cat.spent.toFixed(2)}
            </span>
            <span class="category-limit-val"> / ${curr}${cat.budget_limit.toFixed(2)}</span>
          </div>
          <span class="badge ${isOver ? 'badge-danger' : (pct > 80 ? 'badge-warning' : 'badge-success')}">
            ${cat.percent_used.toFixed(0)}%
          </span>
        </div>
        <div class="progress-container">
          <div class="progress-bar" style="width: ${pct}%; background-color: ${barColor};"></div>
        </div>
      `;
      grid.appendChild(card);
    });

    if (prevFilterVal) {
      selectFilter.value = prevFilterVal;
    }

    // Attach category edit handlers
    grid.querySelectorAll('.edit-cat-btn').forEach(btn => {
      btn.addEventListener('click', () => openEditCategoryModal(btn.getAttribute('data-id')));
    });
  }

  // Load and Render Expenses Table
  async function loadExpenses() {
    const month = selectedMonthInput.value;
    const catId = document.getElementById('txCategoryFilter').value;
    const search = document.getElementById('txSearchInput').value.trim();

    let url = `/api/expenses?month=${month}`;
    if (catId) url += `&category_id=${catId}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;

    const res = await apiCall(url);
    if (!res) return;

    cachedExpenses = res.expenses || [];
    renderExpensesTable(cachedExpenses);
  }

  function renderExpensesTable(expenses) {
    const tbody = document.getElementById('txTableBody');
    const emptyState = document.getElementById('txEmptyState');
    tbody.innerHTML = '';

    const sortVal = document.getElementById('txSortFilter').value;
    const sorted = [...expenses].sort((a, b) => {
      if (sortVal === 'date-desc') return new Date(b.date) - new Date(a.date) || b.id - a.id;
      if (sortVal === 'date-asc') return new Date(a.date) - new Date(b.date) || a.id - b.id;
      if (sortVal === 'amount-desc') return b.amount - a.amount;
      if (sortVal === 'amount-asc') return a.amount - b.amount;
      return 0;
    });

    if (sorted.length === 0) {
      emptyState.style.display = 'block';
      return;
    }

    emptyState.style.display = 'none';
    const curr = currentSummary ? currentSummary.currency : '$';

    sorted.forEach(exp => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td style="white-space: nowrap; font-weight: 500; font-size: 0.82rem; color: var(--text-muted);">
          ${formatDate(exp.date)}
        </td>
        <td>
          <div style="font-weight: 600; color: var(--text-main);">${escapeHtml(exp.title)}</div>
          ${exp.notes ? `<div style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(exp.notes)}</div>` : ''}
        </td>
        <td>
          <span class="tx-cat-badge" style="background-color: ${exp.category_color}18; color: ${exp.category_color};">
            <span>${exp.category_icon}</span> ${escapeHtml(exp.category_name)}
          </span>
        </td>
        <td>
          <span class="tx-pm-chip">${escapeHtml(exp.payment_method)}</span>
        </td>
        <td>
          <span class="tx-amount">${curr}${parseFloat(exp.amount).toFixed(2)}</span>
        </td>
        <td style="text-align: right;">
          <div class="tx-actions" style="justify-content: flex-end;">
            <button class="btn-icon-sm edit-exp-btn" data-id="${exp.id}" title="Edit Expense">✏️</button>
            <button class="btn-icon-sm delete delete-exp-btn" data-id="${exp.id}" title="Delete Expense">🗑️</button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });

    tbody.querySelectorAll('.edit-exp-btn').forEach(b => {
      b.addEventListener('click', () => openEditExpenseModal(b.getAttribute('data-id')));
    });

    tbody.querySelectorAll('.delete-exp-btn').forEach(b => {
      b.addEventListener('click', () => handleDeleteExpense(b.getAttribute('data-id')));
    });
  }

  // Expense Modal Handlers
  function openAddExpenseModal() {
    document.getElementById('expenseModalTitle').innerHTML = '<span>➕</span> Add New Expense';
    document.getElementById('expEditId').value = '';
    document.getElementById('expTitle').value = '';
    document.getElementById('expAmount').value = '';
    document.getElementById('expDate').value = new Date().toISOString().slice(0, 10);
    document.getElementById('expPaymentMethod').value = 'Debit Card';
    document.getElementById('expNotes').value = '';

    openModal(expenseModal);
  }

  function openEditExpenseModal(id) {
    const exp = cachedExpenses.find(e => String(e.id) === String(id));
    if (!exp) return;

    document.getElementById('expenseModalTitle').innerHTML = '<span>✏️</span> Edit Expense';
    document.getElementById('expEditId').value = exp.id;
    document.getElementById('expTitle').value = exp.title;
    document.getElementById('expAmount').value = exp.amount;
    document.getElementById('expDate').value = exp.date;
    document.getElementById('expCategory').value = exp.category_id;
    document.getElementById('expPaymentMethod').value = exp.payment_method;
    document.getElementById('expNotes').value = exp.notes || '';

    openModal(expenseModal);
  }

  async function handleSaveExpense(e) {
    e.preventDefault();
    const editId = document.getElementById('expEditId').value;
    const payload = {
      title: document.getElementById('expTitle').value.trim(),
      amount: parseFloat(document.getElementById('expAmount').value),
      date: document.getElementById('expDate').value,
      category_id: parseInt(document.getElementById('expCategory').value, 10),
      payment_method: document.getElementById('expPaymentMethod').value,
      notes: document.getElementById('expNotes').value.trim()
    };

    if (editId) {
      const res = await apiCall(`/api/expenses/${editId}`, {
        method: 'PUT',
        body: payload
      });
      if (res) {
        showToast('Expense updated!', 'success');
        closeModal(expenseModal);
        loadDashboard();
      }
    } else {
      const res = await apiCall('/api/expenses', {
        method: 'POST',
        body: payload
      });
      if (res) {
        showToast('Expense added!', 'success');
        closeModal(expenseModal);
        loadDashboard();
      }
    }
  }

  async function handleDeleteExpense(id) {
    if (!confirm('Are you sure you want to delete this expense?')) return;
    const res = await apiCall(`/api/expenses/${id}`, { method: 'DELETE' });
    if (res) {
      showToast('Expense removed', 'info');
      loadDashboard();
    }
  }

  // Category Modal Handlers
  function openAddCategoryModal() {
    document.getElementById('categoryModalTitle').innerHTML = '<span>🏷️</span> Add Custom Category';
    document.getElementById('catEditId').value = '';
    document.getElementById('catName').value = '';
    document.getElementById('catIcon').value = '🏷️';
    document.getElementById('catColor').value = '#4F46E5';
    document.getElementById('catLimit').value = '100.00';

    openModal(categoryModal);
  }

  function openEditCategoryModal(id) {
    const cat = cachedCategories.find(c => String(c.id) === String(id));
    if (!cat) return;

    document.getElementById('categoryModalTitle').innerHTML = `<span>✏️</span> Edit Cap: ${cat.name}`;
    document.getElementById('catEditId').value = cat.id;
    document.getElementById('catName').value = cat.name;
    document.getElementById('catIcon').value = cat.icon;
    document.getElementById('catColor').value = cat.color;
    document.getElementById('catLimit').value = cat.budget_limit;

    openModal(categoryModal);
  }

  async function handleSaveCategory(e) {
    e.preventDefault();
    const editId = document.getElementById('catEditId').value;
    const payload = {
      name: document.getElementById('catName').value.trim(),
      icon: document.getElementById('catIcon').value,
      color: document.getElementById('catColor').value,
      budget_limit: parseFloat(document.getElementById('catLimit').value)
    };

    if (editId) {
      const res = await apiCall(`/api/categories/${editId}`, {
        method: 'PUT',
        body: payload
      });
      if (res) {
        showToast('Category updated!', 'success');
        closeModal(categoryModal);
        loadDashboard();
      }
    } else {
      const res = await apiCall('/api/categories', {
        method: 'POST',
        body: payload
      });
      if (res) {
        showToast('New category created!', 'success');
        closeModal(categoryModal);
        loadDashboard();
      }
    }
  }

  // Affordability Reality Check Calculator
  function openAffordabilityModal() {
    document.getElementById('affordItem').value = '';
    document.getElementById('affordPrice').value = '';
    document.getElementById('affordResult').style.display = 'none';
    openModal(affordabilityModal);
  }

  async function handleAffordabilityCheck(e) {
    e.preventDefault();
    const item_name = document.getElementById('affordItem').value.trim();
    const price = parseFloat(document.getElementById('affordPrice').value);

    const res = await apiCall('/api/calculator/affordability', {
      method: 'POST',
      body: { item_name, price }
    });

    if (!res) return;

    const resultBox = document.getElementById('affordResult');
    const verdict = document.getElementById('affordVerdictText');
    const advice = document.getElementById('affordAdviceText');
    const workHours = document.getElementById('affordWorkHours');
    const daysAllow = document.getElementById('affordDaysAllowance');

    verdict.textContent = res.verdict;
    verdict.style.color = res.verdict_class === 'danger' ? 'var(--danger)' : (res.verdict_class === 'caution' ? 'var(--warning)' : 'var(--success)');
    advice.textContent = res.advice;
    workHours.textContent = `${res.hours_of_work} hrs`;
    daysAllow.textContent = `${res.days_of_allowance} days`;

    resultBox.style.display = 'block';
  }

  // Profile Modal & Settings
  function openProfileModal() {
    if (!currentUser) return;
    document.getElementById('profName').value = currentUser.name;
    document.getElementById('profUniversity').value = currentUser.university || '';
    document.getElementById('profMajor').value = currentUser.major || '';
    document.getElementById('profBudget').value = currentUser.monthly_budget;
    document.getElementById('profCurrency').value = currentUser.currency || '$';
    document.getElementById('profWage').value = currentUser.hourly_wage || 16.0;

    openModal(profileModal);
  }

  async function handleSaveProfile(e) {
    e.preventDefault();
    const payload = {
      name: document.getElementById('profName').value.trim(),
      university: document.getElementById('profUniversity').value.trim(),
      major: document.getElementById('profMajor').value.trim(),
      monthly_budget: parseFloat(document.getElementById('profBudget').value),
      currency: document.getElementById('profCurrency').value,
      hourly_wage: parseFloat(document.getElementById('profWage').value)
    };

    const res = await apiCall('/api/auth/profile', {
      method: 'PUT',
      body: payload
    });

    if (res && res.user) {
      currentUser = res.user;
      showToast('Profile updated!', 'success');
      closeModal(profileModal);
      updateNavUser();
      loadDashboard();
    }
  }

  async function handleResetDemo() {
    if (!confirm('Reset sample student expenses and categories back to defaults?')) return;
    const res = await apiCall('/api/auth/reset-demo', { method: 'POST' });
    if (res) {
      showToast('Demo data refreshed!', 'success');
      closeModal(profileModal);
      loadDashboard();
    }
  }

  // Export CSV
  function handleExportCsv() {
    const month = selectedMonthInput.value;
    const url = `/api/export/csv?month=${month}&sbt_token=${token}`;
    window.open(url, '_blank');
  }

  // Helper Modal Open/Close
  function openModal(modal) {
    if (modal) modal.classList.add('active');
  }

  function closeModal(modal) {
    if (modal) modal.classList.remove('active');
  }

  function formatDate(dateStr) {
    if (!dateStr) return '';
    const parts = dateStr.split('-');
    if (parts.length === 3) {
      const d = new Date(parts[0], parts[1] - 1, parts[2]);
      return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
    }
    return dateStr;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // Event Listeners
  function attachEvents() {
    // Brand click
    document.getElementById('brandLogo').addEventListener('click', () => {
      if (token) loadDashboard();
    });

    // Theme toggle
    themeToggleBtn.addEventListener('click', toggleTheme);

    // Auth tabs
    const tabLogin = document.getElementById('tabLoginBtn');
    const tabReg = document.getElementById('tabRegisterBtn');
    tabLogin.addEventListener('click', () => {
      tabLogin.classList.add('active');
      tabReg.classList.remove('active');
      loginForm.style.display = 'block';
      registerForm.style.display = 'none';
    });
    tabReg.addEventListener('click', () => {
      tabReg.classList.add('active');
      tabLogin.classList.remove('active');
      loginForm.style.display = 'none';
      registerForm.style.display = 'block';
    });

    // Forms
    loginForm.addEventListener('submit', handleLogin);
    registerForm.addEventListener('submit', handleRegister);
    document.getElementById('demoLoginBtn').addEventListener('click', handleDemoLogin);
    document.getElementById('logoutBtn').addEventListener('click', () => logout(true));

    // Month Change
    selectedMonthInput.addEventListener('change', () => loadDashboard());

    // Expense Actions
    document.getElementById('navAddExpenseBtn').addEventListener('click', openAddExpenseModal);
    document.getElementById('mainAddExpenseBtn').addEventListener('click', openAddExpenseModal);
    document.getElementById('emptyAddExpenseBtn').addEventListener('click', openAddExpenseModal);
    expenseForm.addEventListener('submit', handleSaveExpense);
    document.getElementById('closeExpenseModalBtn').addEventListener('click', () => closeModal(expenseModal));
    document.getElementById('cancelExpenseModalBtn').addEventListener('click', () => closeModal(expenseModal));

    // Category Actions
    document.getElementById('openAddCategoryBtn').addEventListener('click', openAddCategoryModal);
    categoryForm.addEventListener('submit', handleSaveCategory);
    document.getElementById('closeCategoryModalBtn').addEventListener('click', () => closeModal(categoryModal));
    document.getElementById('cancelCategoryModalBtn').addEventListener('click', () => closeModal(categoryModal));

    // Affordability
    document.getElementById('openAffordabilityBtn').addEventListener('click', openAffordabilityModal);
    affordabilityForm.addEventListener('submit', handleAffordabilityCheck);
    document.getElementById('closeAffordabilityModalBtn').addEventListener('click', () => closeModal(affordabilityModal));
    document.getElementById('cancelAffordabilityBtn').addEventListener('click', () => closeModal(affordabilityModal));

    // Profile & Settings
    document.getElementById('userProfileBtn').addEventListener('click', openProfileModal);
    document.getElementById('cardEditBudgetLink').addEventListener('click', openProfileModal);
    profileForm.addEventListener('submit', handleSaveProfile);
    document.getElementById('closeProfileModalBtn').addEventListener('click', () => closeModal(profileModal));
    document.getElementById('cancelProfileBtn').addEventListener('click', () => closeModal(profileModal));
    document.getElementById('resetDemoBtn').addEventListener('click', handleResetDemo);

    // Export CSV
    document.getElementById('exportCsvBtn').addEventListener('click', handleExportCsv);

    // Filtering & Sorting
    document.getElementById('txSearchInput').addEventListener('input', () => loadExpenses());
    document.getElementById('txCategoryFilter').addEventListener('change', () => loadExpenses());
    document.getElementById('txSortFilter').addEventListener('change', () => renderExpensesTable(cachedExpenses));

    // Close modals on clicking overlay backdrop
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) closeModal(overlay);
      });
    });

    // Close modals with Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.active').forEach(m => closeModal(m));
      }
    });
  }

  // Initialize
  document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    attachEvents();
    initAuth();
  });

})();

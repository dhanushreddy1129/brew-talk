// ============================================
// Brew Talk — Admin App
// ============================================
import { get, post, put, del, adminHeaders } from '/static/shared/js/api.js';
import { SocketManager } from '/static/shared/js/socket.js';
import { formatPrice, timeAgo } from '/static/shared/js/format.js';
import { loadConfig, applyBranding, initTheme, toggleTheme } from '/static/shared/js/theme.js';

let adminKey = '';
let config = {};
let menuItems = [];
let settings = [];
let editingItemId = null;
let eventsLog = [];
let generalSocket = null;

// ── Init ───────────────────────────────────────────────────
async function init() {
  initTheme();
  updateThemeIcon();
  document.getElementById('themeToggle').addEventListener('click', () => {
    toggleTheme(); updateThemeIcon();
  });

  const saved = sessionStorage.getItem('bt-admin-key');
  if (saved) {
    adminKey = saved;
    if (await verifyAuth()) {
      showDashboard();
    } else {
      sessionStorage.removeItem('bt-admin-key');
      showGate();
    }
  } else {
    showGate();
  }
}

function updateThemeIcon() {
  const btn = document.getElementById('themeToggle');
  if (btn) btn.textContent = document.documentElement.getAttribute('data-theme') === 'dark' ? '☀️' : '🌙';
}

function showGate() {
  document.getElementById('passwordGate').style.display = 'flex';
  document.getElementById('gateInput').focus();
}

async function verifyAuth() {
  try {
    await get('/api/orders', adminHeaders(adminKey));
    return true;
  } catch (_) { return false; }
}

window.submitGate = async function() {
  const pwd = document.getElementById('gateInput').value.trim();
  const errEl = document.getElementById('gateError');
  if (!pwd) return;
  try {
    await get('/api/orders', adminHeaders(pwd));
    adminKey = pwd;
    sessionStorage.setItem('bt-admin-key', pwd);
    document.getElementById('passwordGate').style.display = 'none';
    showDashboard();
  } catch (_) {
    errEl.textContent = 'Wrong password. Try again.';
    document.getElementById('gateInput').value = '';
    document.getElementById('gateInput').focus();
  }
};

document.getElementById('gateInput').addEventListener('keydown', e => {
  if (e.key === 'Enter') window.submitGate();
});

async function showDashboard() {
  try {
    config = await loadConfig();
    applyBranding(config);
    document.querySelector('.admin-cafe-name').textContent = config.cafe_name || 'Brew Talk';
  } catch (_) {}

  activateTab('menu');
  setupWebSocket();
  loadMenuTab();
}

// ── Tabs ───────────────────────────────────────────────────
window.activateTab = function(tab) {
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(`tab-${tab}`).classList.add('active');
  document.querySelector(`[data-tab="${tab}"]`).classList.add('active');

  if (tab === 'menu') loadMenuTab();
  else if (tab === 'settings') loadSettingsTab();
  else if (tab === 'qr') loadQRTab();
  else if (tab === 'stats') loadStatsTab();
  // events tab already streams
};

// ── Menu Tab ───────────────────────────────────────────────
async function loadMenuTab() {
  try {
    menuItems = await get('/api/menu');
    renderMenuTable();
  } catch (e) {
    document.getElementById('menuTableBody').innerHTML =
      `<tr><td colspan="8" style="text-align:center;color:var(--color-danger)">Failed to load menu: ${e.message}</td></tr>`;
  }
}

function renderMenuTable() {
  const currency = config.currency || '₹';
  const tbody = document.getElementById('menuTableBody');
  tbody.innerHTML = menuItems.map(item => `
    <tr>
      <td class="emoji-col">
        ${item.image_url ? `<img src="${item.image_url}" alt="${item.name}" style="width:38px;height:38px;border-radius:8px;object-fit:cover;" onerror="this.outerHTML='${item.emoji || '☕'}'" />` : (item.emoji || '🍽')}
      </td>
      <td><strong>${item.name}</strong></td>
      <td><span style="background:var(--color-bg);padding:3px 8px;border-radius:6px;font-size:12px;">${item.category}</span></td>
      <td><strong style="color:var(--color-primary);">${formatPrice(item.price, currency)}</strong></td>
      <td style="max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--color-text-light);font-size:12.5px;">${item.description || '—'}</td>
      <td>
        <span class="avail-badge ${item.available ? 'yes' : 'no'}">
          ${item.available ? '✓ Yes' : '✕ No'}
        </span>
      </td>
      <td>
        <button class="table-action-btn edit-btn" onclick="editItem(${item.id})">Edit</button>
        <button class="table-action-btn delete-btn" onclick="deleteItem(${item.id})">Delete</button>
      </td>
    </tr>`).join('') || `<tr><td colspan="7" style="text-align:center;color:var(--color-text-light)">No items. Add one below!</td></tr>`;
}

window.showAddForm = function() {
  editingItemId = null;
  document.getElementById('formTitle').textContent = '+ Add Menu Item';
  document.getElementById('itemForm').reset();
  document.getElementById('itemAvailable').checked = true;
  document.getElementById('itemFormWrap').style.display = 'block';
  document.getElementById('itemFormWrap').scrollIntoView({ behavior: 'smooth' });
};

window.cancelForm = function() {
  document.getElementById('itemFormWrap').style.display = 'none';
  editingItemId = null;
};

window.editItem = function(id) {
  const item = menuItems.find(i => i.id === id);
  if (!item) return;
  editingItemId = id;
  document.getElementById('formTitle').textContent = `✏ Edit: ${item.name}`;
  document.getElementById('itemName').value = item.name;
  document.getElementById('itemCategory').value = item.category;
  document.getElementById('itemPrice').value = item.price;
  document.getElementById('itemEmoji').value = item.emoji || '';
  document.getElementById('itemDescription').value = item.description || '';
  document.getElementById('itemImageUrl').value = item.image_url || '';
  document.getElementById('itemAvailable').checked = item.available;
  document.getElementById('itemSortOrder').value = item.sort_order || 0;
  document.getElementById('itemFormWrap').style.display = 'block';
  document.getElementById('itemFormWrap').scrollIntoView({ behavior: 'smooth' });
};

window.saveItem = async function() {
  const data = {
    name: document.getElementById('itemName').value.trim(),
    category: document.getElementById('itemCategory').value.trim(),
    price: parseFloat(document.getElementById('itemPrice').value),
    emoji: document.getElementById('itemEmoji').value.trim() || '🍽',
    description: document.getElementById('itemDescription').value.trim(),
    image_url: document.getElementById('itemImageUrl').value.trim(),
    available: document.getElementById('itemAvailable').checked,
    sort_order: parseInt(document.getElementById('itemSortOrder').value || '0'),
  };

  if (!data.name || !data.category || isNaN(data.price)) {
    showToast('Name, category, and price are required.', 'error');
    return;
  }

  try {
    const btn = document.getElementById('saveItemBtn');
    btn.disabled = true; btn.textContent = 'Saving…';
    if (editingItemId) {
      await put(`/api/admin/menu/${editingItemId}`, data, adminHeaders(adminKey));
      showToast('Item updated! ✓', 'success');
    } else {
      await post('/api/admin/menu', data, adminHeaders(adminKey));
      showToast('Item added! ✓', 'success');
    }
    btn.disabled = false; btn.textContent = 'Save Item';
    cancelForm();
    await loadMenuTab();
  } catch (e) {
    showToast('Error: ' + e.message, 'error');
    document.getElementById('saveItemBtn').disabled = false;
    document.getElementById('saveItemBtn').textContent = 'Save Item';
  }
};

window.deleteItem = async function(id) {
  const item = menuItems.find(i => i.id === id);
  if (!confirm(`Delete "${item?.name}"? This cannot be undone.`)) return;
  try {
    await del(`/api/admin/menu/${id}`, adminHeaders(adminKey));
    showToast('Item deleted.', 'info');
    await loadMenuTab();
  } catch (e) {
    showToast('Delete failed: ' + e.message, 'error');
  }
};

// ── Settings Tab ───────────────────────────────────────────
async function loadSettingsTab() {
  try {
    settings = await get('/api/settings', adminHeaders(adminKey));
    renderSettings();
  } catch (e) {
    document.getElementById('settingsContainer').innerHTML =
      `<p style="color:var(--color-danger)">Failed to load settings: ${e.message}</p>`;
  }
}

function renderSettings() {
  const container = document.getElementById('settingsContainer');
  const groups = {};
  settings.forEach(s => {
    groups[s.category] = groups[s.category] || [];
    groups[s.category].push(s);
  });

  // Ensure the AI group exists even if DB rows aren't seeded yet
  if (!groups['ai']) {
    groups['ai'] = [
      { key: 'groq_api_key', value: '', category: 'ai', description: 'Groq API key — get a free key at console.groq.com' },
      { key: 'groq_model',   value: 'llama3-8b-8192', category: 'ai', description: 'Groq model (e.g. llama3-8b-8192, mixtral-8x7b-32768, gemma2-9b-it)' },
    ];
  }

  // Render AI section first with special styling, then the rest
  const aiItems = groups['ai'] || [];
  const otherGroups = Object.entries(groups).filter(([cat]) => cat !== 'ai');

  const aiSection = `
    <div class="settings-group ai-group" style="border:2px solid #7c3aed; border-radius:16px; padding:20px; margin-bottom:24px; background:linear-gradient(135deg,#faf5ff,#f3e8ff);">
      <div class="settings-group-title" style="color:#7c3aed; display:flex; align-items:center; gap:8px;">
        🤖 AI Voice Assistant (Groq)
        <a href="https://console.groq.com/keys" target="_blank" rel="noopener"
           style="font-size:12px; font-weight:500; color:#7c3aed; border:1px solid #7c3aed; border-radius:999px; padding:3px 10px; text-decoration:none; margin-left:auto;">
          Get Free API Key ↗
        </a>
      </div>
      <p style="font-size:13px; color:#6b21a8; margin:0 0 16px 0; line-height:1.5;">
        Paste your Groq API key below to enable intelligent AI voice ordering (Llama 3 / Mixtral). 
        Without a key, the smart keyword fallback is used instead.
      </p>
      ${aiItems.map(s => `
        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-key">${s.key}</div>
            ${s.description ? `<div class="setting-desc">${s.description}</div>` : ''}
          </div>
          <div class="setting-value-wrap">
            ${s.key === 'groq_api_key' ? `
              <div style="display:flex;gap:8px;align-items:center;flex:1;">
                <input class="setting-input" id="setting-${s.key}"
                  type="password" value="${s.value && s.value !== '***' ? s.value : ''}"
                  placeholder="gsk_xxxxxxxxxxxxxxxxxxxx"
                  autocomplete="off" spellcheck="false"
                  aria-label="Groq API key" style="font-family:monospace;" />
                <button onclick="toggleApiKeyVisibility()" title="Show/Hide key"
                  style="padding:6px 10px; border:1px solid #d1d5db; border-radius:8px; background:#fff; cursor:pointer; font-size:16px;" id="toggleApiKeyBtn">👁</button>
              </div>
            ` : `
              <select class="setting-input" id="setting-${s.key}" style="font-family:monospace;">
                ${['llama3-8b-8192','llama3-70b-8192','mixtral-8x7b-32768','gemma2-9b-it','llama-3.1-8b-instant'].map(m =>
                  `<option value="${m}" ${s.value === m ? 'selected' : ''}>${m}</option>`
                ).join('')}
              </select>
            `}
            <button class="setting-save-btn" onclick="saveSetting('${s.key}')" aria-label="Save ${s.key}"
              style="background:#7c3aed; border-color:#7c3aed;">Save</button>
          </div>
        </div>`).join('')}
      <div id="groqStatus" style="margin-top:12px; font-size:13px;"></div>
      <button onclick="testGroqConnection()" style="margin-top:8px; padding:8px 20px; background:#7c3aed; color:#fff; border:none; border-radius:8px; cursor:pointer; font-size:13px; font-weight:600;">
        🧪 Test Groq Connection
      </button>
    </div>`;

  container.innerHTML = aiSection + otherGroups.map(([cat, items]) => `
    <div class="settings-group">
      <div class="settings-group-title">${cat}</div>
      ${items.map(s => `
        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-key">${s.key}</div>
            ${s.description ? `<div class="setting-desc">${s.description}</div>` : ''}
          </div>
          <div class="setting-value-wrap">
            <input class="setting-input" id="setting-${s.key}" value="${s.value}"
              aria-label="Value for ${s.key}" ${s.key.startsWith('color_') ? 'type="text"' : ''}/>
            ${s.key.startsWith('color_') ? `<input type="color" value="${s.value}" 
              oninput="document.getElementById('setting-${s.key}').value=this.value"
              style="width:36px;height:36px;border:none;cursor:pointer;background:none;padding:0;" 
              aria-label="Color picker for ${s.key}" />` : ''}
            <button class="setting-save-btn" onclick="saveSetting('${s.key}')" aria-label="Save ${s.key}">Save</button>
          </div>
        </div>`).join('')}
    </div>`).join('');
}

window.toggleApiKeyVisibility = function() {
  const inp = document.getElementById('setting-groq_api_key');
  const btn = document.getElementById('toggleApiKeyBtn');
  if (!inp) return;
  inp.type = inp.type === 'password' ? 'text' : 'password';
  btn.textContent = inp.type === 'password' ? '👁' : '🙈';
};

window.testGroqConnection = async function() {
  const statusEl = document.getElementById('groqStatus');
  const keyInput = document.getElementById('setting-groq_api_key');
  const key = keyInput?.value?.trim();
  if (!key) {
    statusEl.innerHTML = '<span style="color:#dc2626;">⚠ Paste your Groq API key first, then click Save before testing.</span>';
    return;
  }
  statusEl.innerHTML = '<span style="color:#7c3aed;">Testing connection… ⏳</span>';
  try {
    const result = await post('/api/ai/voice-order', {
      transcript: 'one filter coffee',
      language: 'en-US',
      table_number: 1,
    });
    if (result.cart_actions?.length) {
      statusEl.innerHTML = '<span style="color:#16a34a;">✅ Groq AI is working! Voice orders will use AI.</span>';
    } else {
      statusEl.innerHTML = '<span style="color:#ca8a04;">⚠ Connected but no items matched. Try a different test phrase.</span>';
    }
  } catch (e) {
    statusEl.innerHTML = `<span style="color:#dc2626;">❌ Failed: ${e.message}</span>`;
  }
};

window.saveSetting = async function(key) {
  const input = document.getElementById(`setting-${key}`);
  const value = input.value.trim();
  try {
    await put(`/api/settings/${key}`, { value }, adminHeaders(adminKey));
    showToast(`${key} updated! ✓`, 'success');
    // Reload config to apply changes
    config = await loadConfig();
    applyBranding(config);
  } catch (e) {
    showToast('Failed to save: ' + e.message, 'error');
  }
};

// ── QR Tab ─────────────────────────────────────────────────
function loadQRTab() {
  const totalTables = parseInt(config.total_tables || '12', 10);
  const grid = document.getElementById('qrGrid');
  grid.innerHTML = '';

  for (let i = 1; i <= totalTables; i++) {
    const url = `${location.origin}/m/${i}`;
    const tent = document.createElement('div');
    tent.className = 'qr-tent';
    const cafeName = config.cafe_name || 'Brew Talk';
    tent.innerHTML = `
      <div class="qr-tent-label">🪑 Table ${i}</div>
      <div class="qr-code-wrap" id="qr-wrap-${i}"></div>
      <div class="qr-tent-url">${url}</div>`;
    grid.appendChild(tent);

    // Generate QR code
    setTimeout(() => {
      if (window.QRCode) {
        new QRCode(document.getElementById(`qr-wrap-${i}`), {
          text: url,
          width: 128, height: 128,
          colorDark: config.color_primary || '#3C2415',
          colorLight: '#FFFFFF',
        });
      } else {
        document.getElementById(`qr-wrap-${i}`).innerHTML =
          `<div style="font-size:11px;color:var(--color-text-light);padding:16px;">QR lib loading…</div>`;
      }
    }, 100);
  }
}

window.printQR = function() { window.print(); };

// ── Stats Tab ──────────────────────────────────────────────
async function loadStatsTab() {
  try {
    const stats = await get('/api/admin/stats', adminHeaders(adminKey));
    const currency = config.currency || '₹';
    document.getElementById('statOrders').textContent = stats.total_orders;
    document.getElementById('statRevenue').textContent = formatPrice(stats.total_revenue, currency);
    document.getElementById('statAvg').textContent = stats.total_orders
      ? formatPrice(stats.total_revenue / stats.total_orders, currency)
      : formatPrice(0, currency);

    // Status breakdown
    const statuses = Object.entries(stats.orders_by_status || {});
    document.getElementById('statByStatus').innerHTML = statuses.map(([s, c]) =>
      `<div class="top-item-row"><span class="top-item-name">${s}</span><span class="top-item-qty">${c} orders</span></div>`
    ).join('') || '<p style="color:var(--color-text-light)">No orders today.</p>';

    // Top items
    const topItems = stats.top_items || [];
    document.getElementById('statTopItems').innerHTML = topItems.map((item, idx) =>
      `<div class="top-item-row">
        <span class="top-item-rank">#${idx + 1}</span>
        <span class="top-item-name">${item.item_name}</span>
        <span class="top-item-qty">${item.total_qty} sold</span>
      </div>`).join('') || '<p style="color:var(--color-text-light)">No items ordered today.</p>';
  } catch (e) {
    document.getElementById('statsContent').innerHTML =
      `<p style="color:var(--color-danger)">Failed to load stats: ${e.message}</p>`;
  }
}

// ── WebSocket ──────────────────────────────────────────────
function setupWebSocket() {
  generalSocket = new SocketManager('general', async (msg) => {
    logEvent(msg);
    if (msg.type === 'menu_changed') {
      await loadMenuTab();
    } else if (msg.type === 'settings_changed') {
      config = await loadConfig();
      applyBranding(config);
      document.querySelector('.admin-cafe-name').textContent = config.cafe_name || 'Brew Talk';
    }
  });

  const kitchenSocket = new SocketManager('kitchen', (msg) => {
    logEvent(msg);
  });

  generalSocket.connect();
  kitchenSocket.connect();
}

function logEvent(msg) {
  const log = document.getElementById('eventsLog');
  if (!log) return;
  const time = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const line = document.createElement('div');
  line.className = 'event-line';
  const typeClass = `event-type-${msg.type}`;
  line.innerHTML = `<span class="event-time">[${time}]</span><span class="${typeClass}">${msg.type}</span> <span class="event-json">${JSON.stringify(msg.data || {})}</span>`;
  log.prepend(line);
  // Keep last 200
  while (log.children.length > 200) log.removeChild(log.lastChild);
}

// ── Toast ──────────────────────────────────────────────────
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  toast.setAttribute('role', 'alert');
  document.body.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('visible'));
  setTimeout(() => {
    toast.classList.remove('visible');
    setTimeout(() => toast.remove(), 400);
  }, 3500);
}

init();

// ============================================
// Brew Talk — Kitchen App
// ============================================
import { get, patch, del, adminHeaders } from '/static/shared/js/api.js';
import { SocketManager } from '/static/shared/js/socket.js';
import { timeAgo, formatPrice, formatDate } from '/static/shared/js/format.js';
import { loadConfig, applyBranding, initTheme, toggleTheme, getConfig } from '/static/shared/js/theme.js';

let adminKey = '';
let config = {};
let orders = [];
let kitchenSocket = null;
let timeAgoInterval = null;

// ── Init ───────────────────────────────────────────────────
async function init() {
  initTheme();

  // Password gate
  const saved = sessionStorage.getItem('bt-kitchen-key');
  if (saved) {
    adminKey = saved;
    await startKitchen();
  } else {
    showGate();
  }
}

function showGate() {
  document.getElementById('passwordGate').style.display = 'flex';
  document.getElementById('gateInput').focus();
}

window.submitGate = async function() {
  const pwd = document.getElementById('gateInput').value.trim();
  const errEl = document.getElementById('gateError');
  if (!pwd) return;
  try {
    // Verify by hitting an admin endpoint
    await get('/api/orders', adminHeaders(pwd));
    adminKey = pwd;
    sessionStorage.setItem('bt-kitchen-key', pwd);
    document.getElementById('passwordGate').style.display = 'none';
    await startKitchen();
  } catch (e) {
    errEl.textContent = 'Wrong password. Try again.';
    document.getElementById('gateInput').value = '';
    document.getElementById('gateInput').focus();
  }
};

document.addEventListener('keydown', (e) => {
  if (document.getElementById('passwordGate').style.display !== 'none' && e.key === 'Enter') {
    window.submitGate();
  }
});

async function startKitchen() {
  try {
    config = await loadConfig();
    applyBranding(config);
  } catch (_) {}

  await loadOrders();
  setupWebSocket();

  // Update time-ago every 30s
  timeAgoInterval = setInterval(updateTimeAgo, 30000);

  // Theme toggle
  document.getElementById('themeToggle').addEventListener('click', () => {
    toggleTheme();
    document.getElementById('themeToggle').textContent =
      document.documentElement.getAttribute('data-theme') === 'dark' ? '☀️' : '🌙';
  });
}

// ── Load Orders ────────────────────────────────────────────
async function loadOrders() {
  try {
    const all = await get('/api/orders', adminHeaders(adminKey));
    // Show only active (non-delivered) orders
    orders = all.filter(o => o.status !== 'Delivered' && o.status !== 'Cancelled');
    renderBoard();
  } catch (e) {
    console.error('Failed to load orders:', e);
  }
}

// ── Render Board ───────────────────────────────────────────
function renderBoard() {
  const statusList = (config.order_statuses || 'New,Preparing,Ready,Delivered')
    .split(',')
    .filter(s => s !== 'Delivered');

  const board = document.getElementById('kitchenBoard');
  board.innerHTML = '';

  statusList.forEach((status, idx) => {
    const colOrders = orders.filter(o => o.status === status);
    const col = buildColumn(status, colOrders, statusList, idx);
    board.appendChild(col);
  });

  document.getElementById('orderCount').textContent = orders.length + ' active order' + (orders.length !== 1 ? 's' : '');
}

function buildColumn(status, colOrders, statusList, idx) {
  const colEl = document.createElement('div');
  colEl.className = 'ticket-column';
  colEl.id = `col-${status}`;

  const statusClass = idx === 0 ? 'status-new' : idx === 1 ? 'status-preparing' : 'status-ready';
  const icons = ['🆕', '👨‍🍳', '✅', '🔔'];
  colEl.innerHTML = `
    <div class="column-header ${statusClass}">
      <span>${icons[idx] || '📋'} ${status}</span>
      <span class="column-count">${colOrders.length}</span>
    </div>
    <div class="tickets-list" id="tickets-${status}">
      ${colOrders.length === 0
        ? `<div class="column-empty"><div class="column-empty-icon">🌿</div>No orders</div>`
        : colOrders.map(o => buildTicket(o, statusList)).join('')}
    </div>`;
  return colEl;
}

function buildTicket(order, statusList) {
  const currency = config.currency || '₹';
  const currentIdx = statusList.indexOf(order.status);
  const nextStatus = statusList[currentIdx + 1];
  const nextBtnLabel = nextStatus ? `→ ${nextStatus}` : null;

  const itemsHtml = (order.items || []).map(item =>
    `<div class="ticket-item-row">
      <span>${item.item_name}</span>
      <span>×${item.quantity}</span>
    </div>`).join('');

  const noteHtml = order.note
    ? `<div class="ticket-note">📝 ${order.note}</div>`
    : '';

  const nextBtn = nextBtnLabel
    ? `<button class="ticket-status-btn" onclick="advanceOrder(${order.id}, '${nextStatus}')" aria-label="Mark as ${nextStatus}">
        ${nextBtnLabel}
       </button>`
    : `<button class="ticket-status-btn" style="background:var(--color-success)" onclick="advanceOrder(${order.id}, 'Delivered')" aria-label="Mark as Delivered">
        🏁 Deliver
       </button>`;

  return `
    <div class="ticket-card" id="ticket-${order.id}" role="article" aria-label="Order ${order.id}">
      <div class="ticket-body">
        <div class="ticket-top">
          <span class="ticket-num">#${order.id}</span>
          <span class="ticket-table">Table ${order.table_number}</span>
        </div>
        <div class="ticket-time" data-created="${order.created_at}">${timeAgo(order.created_at)}</div>
        <div class="ticket-items">${itemsHtml}</div>
        ${noteHtml}
        <div class="ticket-total">${formatPrice(order.total, currency)}</div>
        <div class="ticket-actions">
          ${nextBtn}
          <button class="ticket-cancel-btn" onclick="cancelOrder(${order.id})" aria-label="Cancel order ${order.id}">✕</button>
        </div>
      </div>
    </div>`;
}

// ── Actions ────────────────────────────────────────────────
window.advanceOrder = async function(orderId, newStatus) {
  try {
    await patch(`/api/orders/${orderId}/status`, { status: newStatus }, adminHeaders(adminKey));
    await loadOrders();
  } catch (e) {
    alert('Failed to update status: ' + e.message);
  }
};

window.cancelOrder = async function(orderId) {
  if (!confirm(`Cancel order #${orderId}?`)) return;
  try {
    await del(`/api/orders/${orderId}`, adminHeaders(adminKey));
    await loadOrders();
  } catch (e) {
    alert('Failed to cancel order: ' + e.message);
  }
};

// ── WebSocket ──────────────────────────────────────────────
function setupWebSocket() {
  kitchenSocket = new SocketManager('kitchen', async (msg) => {
    if (msg.type === 'order_new') {
      playBeep();
      await loadOrders();
      // Flash the new ticket
      setTimeout(() => {
        const ticket = document.getElementById(`ticket-${msg.data.order_id}`);
        if (ticket) ticket.classList.add('new-ticket');
      }, 100);
    } else if (msg.type === 'order_update') {
      await loadOrders();
    }
  });

  const generalSocket = new SocketManager('general', async (msg) => {
    if (msg.type === 'settings_changed') {
      config = await loadConfig();
      applyBranding(config);
    }
  });
  kitchenSocket.connect();
  generalSocket.connect();
}

// ── Beep (Web Audio API) ───────────────────────────────────
function playBeep() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = ctx.createOscillator();
    const gainNode = ctx.createGain();
    oscillator.connect(gainNode);
    gainNode.connect(ctx.destination);
    oscillator.frequency.setValueAtTime(880, ctx.currentTime);
    oscillator.frequency.setValueAtTime(660, ctx.currentTime + 0.1);
    gainNode.gain.setValueAtTime(0.3, ctx.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);
    oscillator.start(ctx.currentTime);
    oscillator.stop(ctx.currentTime + 0.4);
  } catch (_) {}
}

// ── Time Ago ───────────────────────────────────────────────
function updateTimeAgo() {
  document.querySelectorAll('.ticket-time[data-created]').forEach(el => {
    el.textContent = timeAgo(el.dataset.created);
  });
}

init();

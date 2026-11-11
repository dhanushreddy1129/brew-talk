// ============================================
// Brew Talk — Customer App (Artisan Cafe Edition)
// ============================================
import { get, post } from '/static/shared/js/api.js';
import { SocketManager } from '/static/shared/js/socket.js';
import { formatPrice, timeAgo } from '/static/shared/js/format.js';
import { loadConfig, applyBranding, initTheme, toggleTheme, startConfigPolling, getConfig } from '/static/shared/js/theme.js';

// ── State ──────────────────────────────────────────────────
let tableNumber = 1;
let menuItems = [];
let categories = [];
let activeCategory = null;
let searchQuery = '';
let cart = {}; // { menuItemId: quantity }
let currentOrder = null;
let config = {};
let menuVersion = null;
let recognition = null;
let isListening = false;
let generalSocket = null;
let orderSocket = null;

// ── Web Audio Sound Generator ──────────────────────────────
function playPopSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.type = 'sine';
    osc.frequency.setValueAtTime(440, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.08);
    gain.gain.setValueAtTime(0.15, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.08);
    osc.start();
    osc.stop(ctx.currentTime + 0.08);
  } catch (_) {}
}

function playSuccessChime() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const notes = [523.25, 659.25, 783.99, 1046.50]; // C E G C
    notes.forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.setValueAtTime(freq, ctx.currentTime + idx * 0.1);
      gain.gain.setValueAtTime(0.2, ctx.currentTime + idx * 0.1);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + idx * 0.1 + 0.3);
      osc.start(ctx.currentTime + idx * 0.1);
      osc.stop(ctx.currentTime + idx * 0.1 + 0.3);
    });
  } catch (_) {}
}

// ── Init ───────────────────────────────────────────────────
async function init() {
  initTheme();
  updateThemeIcon();

  // Extract table number from URL /m/{table}
  const match = location.pathname.match(/\/m\/(\d+)/);
  tableNumber = match ? parseInt(match[1], 10) : 1;
  const tableEl = document.getElementById('tableBadge');
  if (tableEl) tableEl.textContent = `Table ${tableNumber}`;
  const receiptTable = document.getElementById('receiptTableLabel');
  if (receiptTable) receiptTable.textContent = `Table ${tableNumber} • Dine In`;

  // Load config & menu
  try {
    config = await loadConfig();
    applyBranding(config);
  } catch (e) {
    config = {};
  }

  await loadMenu();
  setupVoice();
  setupSearch();
  setupCartUI();
  setupWebSocket();
  startPolling();

  // Theme toggle
  document.getElementById('themeToggle').addEventListener('click', () => {
    toggleTheme();
    updateThemeIcon();
  });
}

function updateThemeIcon() {
  const btn = document.getElementById('themeToggle');
  if (btn) btn.textContent = document.documentElement.getAttribute('data-theme') === 'dark' ? '☀️' : '🌙';
}

// ── Menu ───────────────────────────────────────────────────
async function loadMenu() {
  showMenuSkeleton();
  try {
    menuItems = await get('/api/menu?available=true');
    const v = await get('/api/menu/version');
    menuVersion = v.version;
    renderMenu();
  } catch (e) {
    showToast('Failed to load menu', 'error');
    document.getElementById('menuSection').innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">☕</div>
        <div class="empty-state-title">Menu unavailable</div>
        <p>Please check your connection and refresh.</p>
      </div>`;
  }
}

function showMenuSkeleton() {
  const grid = document.getElementById('menuGrid');
  if (grid) {
    grid.innerHTML = Array(6).fill(0).map(() => `<div class="skeleton" style="height:240px; border-radius:20px;"></div>`).join('');
  }
  const bar = document.getElementById('categoryBar');
  if (bar) {
    bar.innerHTML = Array(5).fill(0).map(() =>
      `<div class="skeleton" style="width:80px;height:36px;border-radius:999px;"></div>`).join('');
  }
}

function setupSearch() {
  const searchInput = document.getElementById('menuSearch');
  const clearBtn = document.getElementById('clearSearch');
  if (!searchInput) return;

  searchInput.addEventListener('input', (e) => {
    searchQuery = e.target.value.toLowerCase().trim();
    if (clearBtn) clearBtn.style.display = searchQuery ? 'block' : 'none';
    renderMenu();
  });

  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      searchInput.value = '';
      searchQuery = '';
      clearBtn.style.display = 'none';
      renderMenu();
      searchInput.focus();
    });
  }
}

function renderMenu() {
  // Build categories
  categories = [...new Set(menuItems.map(i => i.category))];
  renderCategoryChips(activeCategory);

  const section = document.getElementById('menuSection');
  if (!section) return;
  section.innerHTML = '';

  let filteredItems = menuItems;

  // Search filter
  if (searchQuery) {
    filteredItems = filteredItems.filter(item =>
      item.name.toLowerCase().includes(searchQuery) ||
      (item.description && item.description.toLowerCase().includes(searchQuery)) ||
      item.category.toLowerCase().includes(searchQuery)
    );
  }

  // Category filter
  if (activeCategory) {
    filteredItems = filteredItems.filter(item => item.category === activeCategory);
  }

  if (filteredItems.length === 0) {
    section.innerHTML = `
      <div style="text-align:center; padding:48px 16px; color:var(--color-text-light);">
        <div style="font-size:44px; margin-bottom:12px;">🔍</div>
        <h3 style="font-family:var(--font-display); font-size:20px; color:var(--color-primary); margin-bottom:6px;">No items found</h3>
        <p style="font-size:14px;">Try searching for "coffee", "dosa", or "tea".</p>
      </div>
    `;
    return;
  }

  // Group by category if viewing all, otherwise show directly
  const activeCategories = [...new Set(filteredItems.map(i => i.category))];

  for (const cat of activeCategories) {
    const items = filteredItems.filter(i => i.category === cat);
    if (!items.length) continue;

    const catEmoji = items[0]?.emoji ? items[0].emoji : '🍽';
    const heading = document.createElement('h2');
    heading.className = 'category-heading';
    heading.innerHTML = `<span>${catEmoji}</span> ${cat} <span style="font-size:13px; font-weight:normal; color:var(--color-text-light); margin-left:auto;">${items.length} items</span>`;
    section.appendChild(heading);

    const grid = document.createElement('div');
    grid.className = 'menu-grid';
    items.forEach(item => grid.appendChild(buildMenuCard(item)));
    section.appendChild(grid);
  }
}

function buildMenuCard(item) {
  const currency = config.currency || '₹';
  const qty = cart[item.id] || 0;
  const card = document.createElement('article');
  card.className = 'menu-card';
  card.dataset.itemId = item.id;

  const fallbackImg = "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=600&q=80";
  const imgUrl = item.image_url || fallbackImg;

  const mediaHtml = `
    <div class="card-media">
      <img src="${imgUrl}" alt="${item.name}" loading="lazy" onerror="this.src='${fallbackImg}'" />
      <div class="card-badge-top">
        <span class="badge-veg"><span class="badge-veg-dot"></span></span>
        <span>${item.emoji || '☕'} ${item.category}</span>
      </div>
    </div>
  `;

  const footerHtml = item.available
    ? qty === 0
      ? `<button class="add-btn" onclick="addToCart(${item.id})" aria-label="Add ${item.name}">+ Add to Tray</button>`
      : `<div class="stepper" role="group" aria-label="Quantity">
          <button class="stepper-btn" onclick="updateCart(${item.id}, -1)" aria-label="Remove one">−</button>
          <span class="stepper-count" aria-live="polite">${qty}</span>
          <button class="stepper-btn" onclick="updateCart(${item.id}, 1)" aria-label="Add one">+</button>
        </div>`
    : `<span class="unavailable-badge" style="background:#FDEAEA; color:#D94F4F; border-radius:999px; padding:4px 10px; font-size:11px; font-weight:700;">Sold Out</span>`;

  card.innerHTML = `
    ${mediaHtml}
    <div class="card-body">
      <h3 class="card-title">${item.name}</h3>
      <p class="card-desc">${item.description || ''}</p>
      <div class="card-footer">
        <span class="card-price">${formatPrice(item.price, currency)}</span>
        ${footerHtml}
      </div>
    </div>`;
  return card;
}

function renderCategoryChips(active = null) {
  const bar = document.getElementById('categoryBar');
  if (!bar) return;
  const allBtn = document.createElement('button');
  allBtn.className = 'chip' + (active === null ? ' active' : '');
  allBtn.innerHTML = `🍽️ All Items`;
  allBtn.onclick = () => {
    activeCategory = null;
    renderMenu();
  };
  bar.innerHTML = '';
  bar.appendChild(allBtn);

  const categoryIcons = {
    'Starters': '🥗',
    'Chinese': '🥢',
    'Rotis & Breads': '🫓',
    'Beverages': '☕',
    'Breakfast': '🥞',
    'Snacks': '🥟',
    'Meals': '🍱',
    'Desserts': '🍨'
  };

  categories.forEach(cat => {
    const btn = document.createElement('button');
    btn.className = 'chip' + (cat === active ? ' active' : '');
    const icon = categoryIcons[cat] || '✨';
    btn.innerHTML = `${icon} ${cat}`;
    btn.onclick = () => {
      activeCategory = cat;
      renderMenu();
    };
    bar.appendChild(btn);
  });
}

// ── Cart Operations ────────────────────────────────────────
window.addToCart = function(id) {
  cart[id] = (cart[id] || 0) + 1;
  playPopSound();
  refreshCartUI();
  updateCardStepper(id);
};

window.updateCart = function(id, delta) {
  cart[id] = (cart[id] || 0) + delta;
  if (cart[id] <= 0) delete cart[id];
  playPopSound();
  refreshCartUI();
  updateCardStepper(id);
};

function updateCardStepper(id) {
  const card = document.querySelector(`.menu-card[data-item-id="${id}"]`);
  if (!card) return;
  const item = menuItems.find(i => i.id === id);
  if (!item) return;
  const footer = card.querySelector('.card-footer');
  const qty = cart[id] || 0;
  const pricePart = footer.querySelector('.card-price').outerHTML;
  footer.innerHTML = pricePart + (qty === 0
    ? `<button class="add-btn" onclick="addToCart(${id})" aria-label="Add ${item.name}">+ Add to Tray</button>`
    : `<div class="stepper" role="group" aria-label="Quantity">
        <button class="stepper-btn" onclick="updateCart(${id}, -1)" aria-label="Remove one">−</button>
        <span class="stepper-count" aria-live="polite">${qty}</span>
        <button class="stepper-btn" onclick="updateCart(${id}, 1)" aria-label="Add one">+</button>
      </div>`);
}

function getCartItems() {
  return Object.entries(cart)
    .filter(([, qty]) => qty > 0)
    .map(([id, qty]) => ({ menu_item_id: parseInt(id), quantity: qty }));
}

function getCartCount() {
  return Object.values(cart).reduce((s, q) => s + q, 0);
}

function setupCartUI() {
  document.getElementById('cartBar')?.addEventListener('click', openCart);
  document.getElementById('cartOverlay')?.addEventListener('click', closeCart);
}

function openCart() {
  document.getElementById('cartOverlay')?.classList.add('open');
  document.getElementById('cartSheet')?.classList.add('open');
  renderReceipt();
}

function closeCart() {
  document.getElementById('cartOverlay')?.classList.remove('open');
  document.getElementById('cartSheet')?.classList.remove('open');
}

async function refreshCartUI() {
  const count = getCartCount();
  const bar = document.getElementById('cartBar');
  if (bar) bar.classList.toggle('visible', count > 0);
  const countEl = document.getElementById('cartCount');
  if (countEl) countEl.textContent = count;

  if (count > 0) {
    try {
      const quote = await post('/api/quote', { items: getCartItems() });
      const totalEl = document.getElementById('cartTotal');
      if (totalEl) totalEl.textContent = formatPrice(quote.total, config.currency || '₹');
      window._lastQuote = quote;
    } catch (_) {}
  }
}

async function renderReceipt() {
  const currency = config.currency || '₹';
  const items = getCartItems();
  if (!items.length) {
    closeCart();
    return;
  }

  let quote = window._lastQuote;
  try {
    quote = await post('/api/quote', { items });
    window._lastQuote = quote;
  } catch (_) {}

  const container = document.getElementById('receiptItems');
  if (!container) return;
  container.innerHTML = '';

  (quote?.items || items.map(i => ({
    menu_item_id: i.menu_item_id,
    quantity: i.quantity,
    name: menuItems.find(m => m.id === i.menu_item_id)?.name || '',
    price: menuItems.find(m => m.id === i.menu_item_id)?.price || 0,
    line_total: (menuItems.find(m => m.id === i.menu_item_id)?.price || 0) * i.quantity
  }))).forEach(item => {
    const menuItem = menuItems.find(m => m.id === item.menu_item_id);
    const row = document.createElement('div');
    row.className = 'receipt-item';
    row.innerHTML = `
      <span style="font-size:22px; flex-shrink:0;">${menuItem?.emoji || '☕'}</span>
      <div class="receipt-item-info">
        <div class="receipt-item-name">${item.name || menuItem?.name}</div>
        <div class="receipt-item-price">${formatPrice(item.price || menuItem?.price, currency)} each</div>
      </div>
      <div style="display:flex; align-items:center; gap:8px;">
        <button class="receipt-qty-btn" onclick="updateCart(${item.menu_item_id}, -1); renderReceipt();">−</button>
        <span style="font-weight:700; min-width:18px; text-align:center;">${cart[item.menu_item_id] || item.quantity}</span>
        <button class="receipt-qty-btn" onclick="updateCart(${item.menu_item_id}, 1); renderReceipt();">+</button>
      </div>
      <div class="receipt-item-total">${formatPrice(item.line_total, currency)}</div>`;
    container.appendChild(row);
  });

  if (quote) {
    document.getElementById('subtotalVal').textContent = formatPrice(quote.subtotal, currency);
    document.getElementById('taxVal').textContent = `${formatPrice(quote.tax_amount, currency)} (${quote.tax_percent}%)`;
    document.getElementById('scVal').textContent = `${formatPrice(quote.service_charge_amount, currency)} (${quote.service_charge_percent}%)`;
    document.getElementById('grandTotalVal').textContent = formatPrice(quote.total, currency);
  }
}

window.placeOrder = async function() {
  const items = getCartItems();
  if (!items.length) return;
  const btn = document.getElementById('placeOrderBtn');
  btn.disabled = true;
  btn.textContent = 'Sending to Kitchen… 🍳';
  const note = document.getElementById('orderNote')?.value || '';
  try {
    const order = await post('/api/orders', { table_number: tableNumber, items, note });
    currentOrder = order;
    sessionStorage.setItem('bt-order', JSON.stringify({ id: order.id, token: order.token }));
    cart = {};
    closeCart();
    refreshCartUI();
    renderMenu();
    playSuccessChime();
    showCelebration();
    showTracker(order);
    connectOrderSocket(order.id, order.token);
    showToast('Order received by Kitchen! 🎉', 'success');
  } catch (e) {
    showToast('Failed to place order: ' + (e.message || 'Unknown error'), 'error');
    btn.disabled = false;
    btn.textContent = 'Place Order to Kitchen ☕';
  }
};

// ── Tracker ────────────────────────────────────────────────
function showTracker(order) {
  const wrap = document.getElementById('trackerWrap');
  if (!wrap) return;
  wrap.classList.add('visible');
  updateTrackerDisplay(order);
  wrap.scrollIntoView({ behavior: 'smooth' });
}

function updateTrackerDisplay(order) {
  const statusList = (config.order_statuses || 'New,Preparing,Ready,Delivered').split(',');
  const labelList = (config.status_labels || statusList.join(',')).split(',');
  const currentIdx = statusList.indexOf(order.status);

  const stepsContainer = document.getElementById('trackerSteps');
  if (stepsContainer) {
    stepsContainer.innerHTML = '';
    statusList.forEach((status, i) => {
      const isDone = i < currentIdx;
      const isActive = i === currentIdx;

      const stepDiv = document.createElement('div');
      stepDiv.style.display = 'flex';
      stepDiv.style.alignItems = 'center';
      stepDiv.style.gap = '6px';

      const step = document.createElement('div');
      step.className = 'tracker-step';
      const icons = ['📋', '👨‍🍳', '✅', '🏁'];
      step.innerHTML = `
        <div class="step-dot ${isDone ? 'done' : isActive ? 'active' : ''}">
          ${isDone ? '✓' : (icons[i] || '⬤')}
        </div>
        <div class="step-label ${isDone ? 'done' : isActive ? 'active' : ''}">${labelList[i] || status}</div>`;
      stepDiv.appendChild(step);

      if (i < statusList.length - 1) {
        const conn = document.createElement('div');
        conn.style.flex = '1';
        conn.style.height = '3px';
        conn.style.background = isDone ? 'var(--color-primary)' : 'var(--color-secondary)';
        conn.style.borderRadius = '2px';
        conn.style.minWidth = '24px';
        conn.style.opacity = isDone ? '1' : '0.4';
        stepDiv.appendChild(conn);
      }
      stepsContainer.appendChild(stepDiv);
    });
  }

  // Update SVG cup fill level
  const fillPct = statusList.length > 1
    ? Math.min(100, Math.round(((currentIdx + 1) / statusList.length) * 100))
    : 0;
  const cup = document.getElementById('cupFill');
  if (cup) cup.style.height = `${fillPct}%`;

  // Info
  const currency = config.currency || '₹';
  document.getElementById('trackerOrderNum').textContent = `Order #${order.id} • Table ${order.table_number}`;
  document.getElementById('trackerStatus').textContent = labelList[currentIdx] || order.status;
  document.getElementById('trackerTotal').textContent = formatPrice(order.total, currency);
}

function connectOrderSocket(orderId, token) {
  if (orderSocket) orderSocket.close();
  orderSocket = new SocketManager(`orders_${orderId}`, async (msg) => {
    if (msg.type === 'order_update' && msg.data.order_id === orderId) {
      try {
        const updated = await get(`/api/orders/${orderId}?token=${token}`);
        updateTrackerDisplay(updated);
        showToast(`Order status: ${updated.status}`, 'info');
      } catch (_) {}
    }
  });
  orderSocket.connect();
}

// ── Voice Ordering ─────────────────────────────────────────
function setupVoice() {
  const micBtn = document.getElementById('micBtn');
  if (micBtn) micBtn.addEventListener('click', toggleListening);

  document.getElementById('typedSendBtn')?.addEventListener('click', () => {
    const input = document.getElementById('typedInput');
    const text = input.value.trim();
    if (text) {
      processTranscript(text);
      input.value = '';
    }
  });
  document.getElementById('typedInput')?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      document.getElementById('typedSendBtn').click();
    }
  });

  // Check mic availability at startup and show typed fallback if speech unavailable
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    if (micBtn) {
      micBtn.title = 'Speech not supported — please type your order';
      micBtn.style.opacity = '0.5';
    }
    setBubble('Voice ordering works in Chrome/Edge. Use the text box below to type your order! ⌨️');
  }
}

window.simulateVoice = function(promptText) {
  const input = document.getElementById('typedInput');
  if (input) input.value = promptText;
  processTranscript(promptText);
};

// ── Voice Ordering System (Dual SpeechRecognition + MediaRecorder Fallback) ──
let mediaStream = null;
let mediaRecorder = null;
let recordedAudioChunks = [];
let speechBuffer = '';
let _speechProcessed = false;
let _userWantsToListen = false;
let _autoStopTimer = null;
let _silenceTimer = null;
let _listenLang = 'en-US';

function _setVoiceUI(listening) {
  isListening = listening;
  const btn = document.getElementById('micBtn');
  if (btn) {
    btn.classList.toggle('listening', listening);
    btn.setAttribute('aria-label', listening ? 'Stop listening' : 'Start voice ordering');
  }
  const wave = document.getElementById('voiceWaveform');
  if (wave) wave.style.display = listening ? 'flex' : 'none';
  const icon = document.getElementById('micIcon');
  if (icon) icon.textContent = listening ? '🛑' : '🎙';
}

function toggleListening() {
  if (isListening) {
    stopListeningAndProcess();
  } else {
    startListening();
  }
}

async function startListening() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  // Reset state
  speechBuffer = '';
  _speechProcessed = false;
  _userWantsToListen = true;
  recordedAudioChunks = [];
  clearTimeout(_autoStopTimer);
  clearTimeout(_silenceTimer);

  const langSelect = document.getElementById('langSelect');
  _listenLang = (langSelect && langSelect.value) ? langSelect.value : 'en-US';

  // Instant visual feedback
  _setVoiceUI(true);
  const tText = document.getElementById('transcriptText');
  if (tText) tText.textContent = 'Listening… speak clearly into your mic';
  const tHint = document.getElementById('transcriptHint');
  if (tHint) tHint.textContent = 'Speak your full order. Tap 🛑 when done!';
  setBubble('I\'m listening in English! Say e.g. "two butter naan and one chilli paneer" 👂', true);

  // 1. Request microphone stream via getUserMedia (triggers browser permission dialog if needed)
  try {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Start MediaRecorder as guaranteed audio backup
      try {
        const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
          ? 'audio/webm;codecs=opus'
          : (MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4');
        mediaRecorder = new MediaRecorder(mediaStream, { mimeType });
        recordedAudioChunks = [];
        mediaRecorder.ondataavailable = (e) => {
          if (e.data && e.data.size > 0) recordedAudioChunks.push(e.data);
        };
        mediaRecorder.start(250); // collect chunks every 250ms
      } catch (recErr) {
        console.warn('[audio] MediaRecorder not available:', recErr);
        mediaRecorder = null;
      }
    }
  } catch (err) {
    console.warn('[audio] getUserMedia error:', err);
    if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
      _setVoiceUI(false);
      _userWantsToListen = false;
      setBubble('🔒 Mic permission is blocked. Please click the lock or camera icon in the browser address bar to Allow Microphone!');
      showToast('Microphone access blocked. Click address bar lock to allow 🔒', 'error');
      return;
    }
  }

  // 2. Start Web Speech Recognition if supported
  if (SpeechRecognition) {
    try {
      if (recognition) { try { recognition.abort(); } catch (_) {} }
      recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = _listenLang;
      recognition.maxAlternatives = 3;

      recognition.onstart = () => {
        if (!_userWantsToListen) {
          try { recognition.abort(); } catch (_) {}
          return;
        }
      };

      recognition.onresult = (e) => {
        let interim = '';
        let finalChunk = '';
        for (let i = e.resultIndex; i < e.results.length; ++i) {
          const res = e.results[i];
          if (res.isFinal) finalChunk += res[0].transcript;
          else interim += res[0].transcript;
        }
        if (finalChunk) speechBuffer += (speechBuffer ? ' ' : '') + finalChunk.trim();

        const currentDisplay = speechBuffer || interim;
        const textEl = document.getElementById('transcriptText');
        if (textEl && currentDisplay) {
          textEl.textContent = `"${currentDisplay}"`;
        }

        // Auto-complete after 2.5 seconds of silence following final speech
        if (finalChunk) {
          clearTimeout(_silenceTimer);
          _silenceTimer = setTimeout(() => {
            if (_userWantsToListen && speechBuffer.trim()) {
              stopListeningAndProcess();
            }
          }, 2500);
        }
      };

      recognition.onerror = (e) => {
        console.warn('[speech] recognition error event:', e.error);
        if (e.error === 'not-allowed') {
          setBubble('🔒 Mic access not allowed. Please allow mic in browser settings.');
        } else if (e.error === 'network') {
          // Web speech network error — MediaRecorder backup will handle it
          console.log('[speech] Falling back to audio recording');
        }
      };

      recognition.onend = () => {
        // If user is still listening and continuous dropped prematurely, restart Web Speech
        if (_userWantsToListen && !speechBuffer.trim()) {
          try {
            recognition.start();
          } catch (_) {}
        }
      };

      recognition.start();
    } catch (e) {
      console.warn('[speech] Failed to start Web Speech API:', e);
    }
  }
}

async function stopListeningAndProcess() {
  _userWantsToListen = false;
  clearTimeout(_autoStopTimer);
  clearTimeout(_silenceTimer);
  _setVoiceUI(false);

  // Stop Web Speech
  if (recognition) {
    try { recognition.stop(); } catch (_) {}
  }

  // Stop MediaRecorder
  let recordedBlob = null;
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    await new Promise((resolve) => {
      mediaRecorder.onstop = () => {
        try {
          recordedBlob = new Blob(recordedAudioChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
        } catch (_) {}
        resolve();
      };
      try { mediaRecorder.stop(); } catch (_) { resolve(); }
    });
  }

  // Release mic tracks
  if (mediaStream) {
    mediaStream.getTracks().forEach(t => t.stop());
    mediaStream = null;
  }

  const raw = speechBuffer.trim();

  // Route 1: We have text from Web Speech API
  if (raw && !_speechProcessed) {
    _speechProcessed = true;
    processTranscript(raw);
    return;
  }

  // Route 2: Web Speech didn't capture text, but we have recorded audio from MediaRecorder
  if (recordedBlob && recordedBlob.size > 1000 && !_speechProcessed) {
    _speechProcessed = true;
    setBubble('Processing recorded voice with AI… 🎙', true);
    document.getElementById('transcriptText').textContent = 'Transcribing voice…';
    try {
      const reader = new FileReader();
      reader.onloadend = async () => {
        const base64Audio = reader.result.split(',')[1];
        if (!base64Audio) {
          setBubble('No audio was captured. Tap the mic and speak clearly 😊');
          return;
        }
        try {
          const result = await post('/api/ai/audio-order', {
            audio_base64: base64Audio,
            mime_type: recordedBlob.type || 'audio/webm',
            language: _listenLang,
            table_number: tableNumber,
          });
          handleAIOrderResult(result);
        } catch (err) {
          setBubble('Could not process audio. Try typing your order or use the quick buttons below!');
        }
      };
      reader.readAsDataURL(recordedBlob);
      return;
    } catch (err) {
      console.warn('FileReader failed:', err);
    }
  }

  // Route 3: Neither had input
  const tHint = document.getElementById('transcriptHint');
  if (tHint) tHint.textContent = 'Tap mic to speak your order in English';
  setBubble('Nothing heard. Tap 🎙 and speak your full order clearly, or tap the quick buttons below! 😊');
}

function _speakReply(text) {
  if (!('speechSynthesis' in window) || !text) return;
  // Delay to allow audio resources to release
  setTimeout(() => {
    try {
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(text);
      utter.lang = 'en-US';
      utter.rate = 0.95;
      utter.pitch = 1.0;
      const voices = window.speechSynthesis.getVoices();
      const preferred = voices.find(v => v.lang === 'en-US' && v.name.includes('Google'))
        || voices.find(v => v.lang.startsWith('en') && !v.name.includes('Male'))
        || voices.find(v => v.lang.startsWith('en'))
        || null;
      if (preferred) utter.voice = preferred;
      window.speechSynthesis.speak(utter);
    } catch (_) {}
  }, 250);
}

function handleAIOrderResult(result) {
  setBubble(result.reply || 'Added to your tray!');
  _speakReply(result.reply);

  if (result.cart_actions?.length) {
    result.cart_actions.forEach(action => {
      if (action.action === 'add') {
        cart[action.menu_item_id] = (cart[action.menu_item_id] || 0) + action.quantity;
      } else if (action.action === 'remove') {
        cart[action.menu_item_id] = Math.max(0, (cart[action.menu_item_id] || 0) - action.quantity);
        if (cart[action.menu_item_id] === 0) delete cart[action.menu_item_id];
      } else if (action.action === 'set') {
        if (action.quantity <= 0) delete cart[action.menu_item_id];
        else cart[action.menu_item_id] = action.quantity;
      }
    });
    playPopSound();
    refreshCartUI();
    renderMenu();
    showToast('Added items to tray! ☕', 'success');
  }
}

async function processTranscript(transcript) {
  const langSelect = document.getElementById('langSelect');
  const lang = (langSelect && langSelect.value) ? langSelect.value : 'en-US';
  setBubble('Finding your items… 🍳', true);
  try {
    const result = await post('/api/ai/voice-order', {
      transcript,
      language: lang,
      table_number: tableNumber,
    });
    handleAIOrderResult(result);
  } catch (e) {
    setBubble('Sorry, I had trouble with that request. Could you try again?');
  }
}

function setBubble(text, typing = false) {
  const bubble = document.getElementById('speechBubble');
  if (!bubble) return;
  bubble.className = 'speech-bubble' + (typing ? ' typing' : '');
  bubble.innerHTML = text;
}

// ── WebSocket ──────────────────────────────────────────────
function setupWebSocket() {
  generalSocket = new SocketManager('general', async (msg) => {
    if (msg.type === 'menu_changed') {
      await loadMenu();
      refreshCartUI();
    } else if (msg.type === 'settings_changed') {
      config = await loadConfig();
      applyBranding(config);
      refreshCartUI();
    }
  });
  generalSocket.connect();
}

// ── Polling ────────────────────────────────────────────────
function startPolling() {
  startConfigPolling(async (newConfig) => {
    config = newConfig;
    applyBranding(config);
    refreshCartUI();
  });

  // Menu version polling
  setInterval(async () => {
    try {
      const { version } = await get('/api/menu/version');
      if (menuVersion && version !== menuVersion) {
        menuVersion = version;
        await loadMenu();
        refreshCartUI();
      } else {
        menuVersion = version;
      }
    } catch (_) {}
  }, 3000);
}

// ── Celebration ────────────────────────────────────────────
function showCelebration() {
  const el = document.getElementById('celebration');
  if (!el) return;
  const colors = ['#7FB685', '#D4A574', '#3C2415', '#F5A623', '#D94F4F', '#FDF6EC'];
  for (let i = 0; i < 60; i++) {
    const piece = document.createElement('div');
    piece.className = 'confetti-piece';
    piece.style.position = 'fixed';
    piece.style.left = Math.random() * 100 + 'vw';
    piece.style.top = '-20px';
    piece.style.background = colors[Math.floor(Math.random() * colors.length)];
    piece.style.borderRadius = Math.random() > 0.5 ? '50%' : '3px';
    piece.style.animation = `confetti-fall ${2 + Math.random() * 2}s ease-in forwards`;
    piece.style.animationDelay = Math.random() * 0.8 + 's';
    piece.style.width = piece.style.height = (6 + Math.random() * 8) + 'px';
    piece.style.zIndex = '99999';
    el.appendChild(piece);
  }
  setTimeout(() => { el.innerHTML = ''; }, 4500);
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
window.showToast = showToast;

init();

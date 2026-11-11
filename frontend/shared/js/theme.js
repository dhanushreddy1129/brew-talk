// ============================================
// Brew Talk — Theme & Config Manager
// ============================================

let _config = null;
let _pollInterval = null;
let _lastVersion = null;

/**
 * Fetch /api/config and cache it.
 * @returns {Promise<Object>} flat key-value config
 */
export async function loadConfig() {
  const res = await fetch('/api/config');
  if (!res.ok) throw new Error('Failed to load config');
  const json = await res.json();
  // API returns { config: { key: value } }
  _config = json.config || json;
  applyColors(_config);
  applyFavicon(_config);
  return _config;
}

/**
 * Return cached config (call loadConfig first).
 * @returns {Object|null}
 */
export function getConfig() {
  return _config;
}

/**
 * Apply color CSS variables from config to :root.
 * @param {Object} config
 */
export function applyColors(config) {
  const root = document.documentElement;
  const colorMap = {
    color_primary: '--color-primary',
    color_secondary: '--color-secondary',
    color_accent: '--color-accent',
    color_background: '--color-bg',
    color_surface: '--color-surface',
    color_text: '--color-text',
    color_text_light: '--color-text-light',
  };
  for (const [key, cssVar] of Object.entries(colorMap)) {
    if (config[key]) root.style.setProperty(cssVar, config[key]);
  }
}

/**
 * Update document title and any .cafe-name elements with the cafe name.
 * @param {Object} config
 */
export function applyBranding(config) {
  if (config.cafe_name) {
    document.title = config.cafe_name;
    document.querySelectorAll('.cafe-name').forEach(el => {
      el.textContent = config.cafe_name;
    });
  }
  if (config.cafe_tagline) {
    document.querySelectorAll('.cafe-tagline').forEach(el => {
      el.textContent = config.cafe_tagline;
    });
  }
}

/**
 * Set favicon emoji if supported.
 */
function applyFavicon(config) {
  try {
    const canvas = document.createElement('canvas');
    canvas.width = 32; canvas.height = 32;
    const ctx = canvas.getContext('2d');
    ctx.font = '28px serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('☕', 16, 16);
    const link = document.querySelector("link[rel~='icon']") || document.createElement('link');
    link.rel = 'icon';
    link.href = canvas.toDataURL();
    document.head.appendChild(link);
  } catch (_) {}
}

/**
 * Toggle dark/light mode.
 */
export function toggleTheme() {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const next = isDark ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('bt-theme', next);
  return next;
}

/**
 * Load saved theme preference from localStorage.
 */
export function initTheme() {
  const saved = localStorage.getItem('bt-theme');
  if (saved) {
    document.documentElement.setAttribute('data-theme', saved);
  } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.documentElement.setAttribute('data-theme', 'dark');
  }
}

/**
 * Poll /api/config/version every 3 seconds.
 * If the version changes, reload config and call callback.
 * @param {Function} callback - called with new config when changed
 */
export function startConfigPolling(callback) {
  if (_pollInterval) clearInterval(_pollInterval);
  _pollInterval = setInterval(async () => {
    try {
      const res = await fetch('/api/config/version');
      if (!res.ok) return;
      const { version } = await res.json();
      if (_lastVersion && version !== _lastVersion) {
        const newConfig = await loadConfig();
        if (callback) callback(newConfig);
      }
      _lastVersion = version;
    } catch (_) {}
  }, 3000);
  // Set initial version
  fetch('/api/config/version')
    .then(r => r.json())
    .then(({ version }) => { _lastVersion = version; })
    .catch(() => {});
}

/**
 * Stop config polling.
 */
export function stopConfigPolling() {
  if (_pollInterval) {
    clearInterval(_pollInterval);
    _pollInterval = null;
  }
}

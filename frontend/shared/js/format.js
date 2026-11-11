// ============================================
// Brew Talk — Formatting Utilities
// ============================================

/**
 * Format a price with the given currency symbol.
 * @param {number} amount
 * @param {string} currency - e.g. '₹'
 * @returns {string} e.g. '₹120.00'
 */
export function formatPrice(amount, currency = '₹') {
  if (amount == null || isNaN(amount)) return `${currency}0.00`;
  return `${currency}${Number(amount).toFixed(2)}`;
}

/**
 * Format a date/datetime string to a human-readable "time ago" string.
 * @param {string} dateString - ISO date string
 * @returns {string} e.g. 'just now', '2 min ago', '1 hr ago'
 */
export function timeAgo(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString.endsWith('Z') ? dateString : dateString + 'Z');
  const now = new Date();
  const diffMs = now - date;
  const diffSec = Math.floor(diffMs / 1000);

  if (diffSec < 10) return 'just now';
  if (diffSec < 60) return `${diffSec}s ago`;
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin} min ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr} hr ago`;
  const diffDay = Math.floor(diffHr / 24);
  return `${diffDay}d ago`;
}

/**
 * Format a date string to a readable date/time.
 * @param {string} dateString
 * @returns {string} e.g. '11 Nov, 3:45 PM'
 */
export function formatDate(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString.endsWith('Z') ? dateString : dateString + 'Z');
  return date.toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  });
}

/**
 * Truncate text with ellipsis.
 * @param {string} text
 * @param {number} maxLen
 * @returns {string}
 */
export function truncate(text, maxLen = 60) {
  if (!text || text.length <= maxLen) return text || '';
  return text.slice(0, maxLen - 1) + '…';
}

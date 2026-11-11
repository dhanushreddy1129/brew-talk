// ============================================
// Brew Talk — API Helper Module
// ============================================

const BASE = ''; // same origin

/**
 * GET request
 * @param {string} path - API path (e.g. '/api/menu')
 * @param {Object} headers - Additional headers
 * @returns {Promise<any>}
 */
export async function get(path, headers = {}) {
  const res = await fetch(BASE + path, {
    method: 'GET',
    headers: { ...headers },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

/**
 * POST request
 * @param {string} path - API path
 * @param {Object} body - JSON body
 * @param {Object} headers - Additional headers
 * @returns {Promise<any>}
 */
export async function post(path, body, headers = {}) {
  const res = await fetch(BASE + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...headers },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

/**
 * PUT request
 * @param {string} path - API path
 * @param {Object} body - JSON body
 * @param {Object} headers - Additional headers
 * @returns {Promise<any>}
 */
export async function put(path, body, headers = {}) {
  const res = await fetch(BASE + path, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...headers },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

/**
 * PATCH request
 * @param {string} path - API path
 * @param {Object} body - JSON body
 * @param {Object} headers - Additional headers
 * @returns {Promise<any>}
 */
export async function patch(path, body, headers = {}) {
  const res = await fetch(BASE + path, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...headers },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

/**
 * DELETE request
 * @param {string} path - API path
 * @param {Object} headers - Additional headers
 * @returns {Promise<any>}
 */
export async function del(path, headers = {}) {
  const res = await fetch(BASE + path, {
    method: 'DELETE',
    headers: { ...headers },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${text}`);
  }
  // Some DELETE endpoints return 204 No Content
  if (res.status === 204) return null;
  return res.json();
}

/**
 * Build admin auth headers
 * @param {string} password - Admin password/key
 * @returns {Object} Headers with X-Admin-Key
 */
export function adminHeaders(password) {
  return { 'X-Admin-Key': password };
}

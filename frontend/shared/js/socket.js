// ============================================
// Brew Talk — WebSocket Manager
// ============================================

export class SocketManager {
  /**
   * @param {string} channel - WebSocket channel name (e.g. 'general', 'kitchen', 'orders_123')
   * @param {function} onMessage - Callback for parsed JSON messages: (data) => void
   */
  constructor(channel, onMessage) {
    this.channel = channel;
    this.onMessage = onMessage;
    this.ws = null;
    this.reconnectTimer = null;
    this.reconnectDelay = 2000;
    this.maxReconnectDelay = 30000;
    this.currentDelay = this.reconnectDelay;
    this.intentionallyClosed = false;
    this.banner = null;
    this._ensureBanner();
  }

  /** Create or find the reconnecting banner element */
  _ensureBanner() {
    this.banner = document.getElementById('reconnecting-banner');
    if (!this.banner) {
      this.banner = document.createElement('div');
      this.banner.id = 'reconnecting-banner';
      this.banner.className = 'reconnecting-banner';
      this.banner.setAttribute('role', 'alert');
      this.banner.setAttribute('aria-live', 'polite');
      this.banner.innerHTML = `
        <span class="spinner-dot"></span>
        <span class="spinner-dot"></span>
        <span class="spinner-dot"></span>
        <span>Reconnecting…</span>
      `;
      document.body.prepend(this.banner);
    }
  }

  /** Show the reconnecting banner */
  _showBanner() {
    if (this.banner) {
      this.banner.classList.add('visible');
    }
  }

  /** Hide the reconnecting banner */
  _hideBanner() {
    if (this.banner) {
      this.banner.classList.remove('visible');
    }
  }

  /** Establish WebSocket connection */
  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
      return;
    }

    this.intentionallyClosed = false;
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${location.host}/ws/${this.channel}`;

    try {
      this.ws = new WebSocket(url);
    } catch (err) {
      console.error(`[WS ${this.channel}] Failed to create WebSocket:`, err);
      this._scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      console.log(`[WS ${this.channel}] Connected`);
      this._hideBanner();
      this.currentDelay = this.reconnectDelay; // reset backoff
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.onMessage(data);
      } catch (err) {
        console.warn(`[WS ${this.channel}] Invalid message:`, event.data, err);
      }
    };

    this.ws.onclose = (event) => {
      console.log(`[WS ${this.channel}] Closed (code: ${event.code})`);
      if (!this.intentionallyClosed) {
        this._showBanner();
        this._scheduleReconnect();
      }
    };

    this.ws.onerror = (err) => {
      console.error(`[WS ${this.channel}] Error:`, err);
      // onclose will fire after onerror, triggering reconnect
    };
  }

  /** Schedule automatic reconnection with exponential backoff */
  _scheduleReconnect() {
    if (this.intentionallyClosed) return;

    clearTimeout(this.reconnectTimer);
    this.reconnectTimer = setTimeout(() => {
      console.log(`[WS ${this.channel}] Reconnecting (delay: ${this.currentDelay}ms)...`);
      this.connect();
    }, this.currentDelay);

    // Exponential backoff
    this.currentDelay = Math.min(this.currentDelay * 1.5, this.maxReconnectDelay);
  }

  /** Send a message over the WebSocket */
  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn(`[WS ${this.channel}] Cannot send, not connected`);
    }
  }

  /** Intentionally close the connection */
  close() {
    this.intentionallyClosed = true;
    clearTimeout(this.reconnectTimer);
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this._hideBanner();
  }
}

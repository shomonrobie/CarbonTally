/**
 * Event Dispatcher
 * Centralized event handling for Realtime
 */

export class EventDispatcher {
  constructor() {
    this.listeners = new Map();
  }

  /**
   * Register event listener
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
    return () => this.off(event, callback);
  }

  /**
   * Remove event listener
   */
  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index !== -1) {
        callbacks.splice(index, 1);
      }
      if (callbacks.length === 0) {
        this.listeners.delete(event);
      }
    }
  }

  /**
   * Dispatch event
   */
  dispatch(event, payload) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      for (const callback of callbacks) {
        try {
          callback(payload);
        } catch (error) {
          console.error(`Error in event handler for ${event}:`, error);
        }
      }
    }
  }

  /**
   * Clear all listeners
   */
  clear() {
    this.listeners.clear();
  }
}
/**
 * Realtime Manager
 * Centralized Supabase Realtime connection manager
 */

import { createClient } from '@supabase/supabase-js';
import { EventTypes, Tables } from './types';

// ✅ Get credentials from environment
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.REACT_APP_SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.REACT_APP_SUPABASE_ANON_KEY;

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.error('❌ Supabase credentials missing! Check your environment variables.');
}

class RealtimeManager {
  constructor() {
    // ✅ Initialize with environment variables
    this.supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
    this.channels = new Map();
    this.listeners = new Map();
    this.eventDispatcher = new EventDispatcher();
    this.isConnected = false;
    this.user = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectDelay = 1000;
  }

  /**
   * Initialize with user data
   */
  initialize(user) {
    this.user = user;
    
    // Set auth token from user session
    if (user?.accessToken) {
      this.supabase.auth.setSession({
        access_token: user.accessToken,
        refresh_token: user.refreshToken,
      });
    }

    console.log('🔑 Realtime initialized for user:', user?.email || 'unknown');
  }

  /**
   * Connect to Realtime
   */
  async connect() {
    if (!this.user) {
      console.warn('⚠️ Realtime: No user to connect. Call initialize() first.');
      return;
    }

    if (this.isConnected) {
      console.log('ℹ️ Realtime already connected');
      return;
    }

    try {
      console.log('🔌 Connecting to Realtime...');

      // Connect to organization channel
      const orgChannel = await this.connectOrganizationChannel(this.user.organization_id);
      this.channels.set(`org:${this.user.organization_id}`, orgChannel);

      // Connect to staff channel if user is staff
      if (this.user.isStaff) {
        const staffChannel = await this.connectStaffChannel(this.user.id);
        this.channels.set(`staff:${this.user.id}`, staffChannel);
      }

      // Connect to active conversation channels
      const activeConversations = await this.getActiveConversations();
      for (const conv of activeConversations) {
        const convChannel = await this.connectConversationChannel(conv.id);
        this.channels.set(`conversation:${conv.id}`, convChannel);
      }

      this.isConnected = true;
      this.reconnectAttempts = 0;
      console.log('✅ Realtime connected successfully!');
      this.eventDispatcher.dispatch('CONNECTED', { user: this.user });
    } catch (error) {
      console.error('❌ Realtime connection error:', error);
      this.eventDispatcher.dispatch('ERROR', { error });
      this.handleReconnect();
    }
  }

  /**
   * Handle reconnection with exponential backoff
   */
  handleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('❌ Max reconnect attempts reached. Please refresh the page.');
      this.eventDispatcher.dispatch('MAX_RECONNECT_ATTEMPTS', {});
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts), 30000);
    
    console.log(`🔄 Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Connect to Organization Channel
   */
  async connectOrganizationChannel(orgId) {
    const channelName = `org:${orgId}`;
    const channel = this.supabase.channel(channelName);

    // Subscribe to notifications
    channel.on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: Tables.NOTIFICATIONS,
      filter: `organization_id=eq.${orgId}`,
    }, (payload) => {
      console.log('🔔 New notification:', payload.new);
      this.eventDispatcher.dispatch(EventTypes.NOTIFICATION_INSERT, payload);
    });

    // Subscribe to notifications updates (read status)
    channel.on('postgres_changes', {
      event: 'UPDATE',
      schema: 'public',
      table: Tables.NOTIFICATIONS,
      filter: `organization_id=eq.${orgId}`,
    }, (payload) => {
      this.eventDispatcher.dispatch(EventTypes.NOTIFICATION_UPDATE, payload);
    });

    // Subscribe to document updates
    channel.on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: Tables.CUSTOMER_DOCUMENTS,
      filter: `organization_id=eq.${orgId}`,
    }, (payload) => {
      console.log('📄 New document:', payload.new.file_name);
      this.eventDispatcher.dispatch(EventTypes.DOCUMENT_INSERT, payload);
    });

    channel.on('postgres_changes', {
      event: 'UPDATE',
      schema: 'public',
      table: Tables.CUSTOMER_DOCUMENTS,
      filter: `organization_id=eq.${orgId}`,
    }, (payload) => {
      console.log(`📄 Document ${payload.new.id} status: ${payload.new.status}`);
      this.eventDispatcher.dispatch(EventTypes.DOCUMENT_UPDATE, payload);
    });

    // Subscribe to verification updates
    channel.on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: Tables.CUSTOMER_VERIFICATIONS,
      filter: `organization_id=eq.${orgId}`,
    }, (payload) => {
      this.eventDispatcher.dispatch(EventTypes.VERIFICATION_INSERT, payload);
    });

    channel.on('postgres_changes', {
      event: 'UPDATE',
      schema: 'public',
      table: Tables.CUSTOMER_VERIFICATIONS,
      filter: `organization_id=eq.${orgId}`,
    }, (payload) => {
      this.eventDispatcher.dispatch(EventTypes.VERIFICATION_UPDATE, payload);
    });

    // Subscribe to activity feed
    channel.on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: Tables.ACTIVITY_FEED,
      filter: `organization_id=eq.${orgId}`,
    }, (payload) => {
      this.eventDispatcher.dispatch(EventTypes.ACTIVITY_INSERT, payload);
    });

    // Subscribe to messages
    channel.on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: Tables.MESSAGES,
      filter: `organization_id=eq.${orgId}`,
    }, (payload) => {
      this.eventDispatcher.dispatch(EventTypes.MESSAGE_INSERT, payload);
    });

    // Subscribe to queue updates (for staff)
    if (this.user?.isStaff) {
      channel.on('postgres_changes', {
        event: 'UPDATE',
        schema: 'public',
        table: Tables.MANUAL_REVIEW_QUEUE,
        filter: `organization_id=eq.${orgId}`,
      }, (payload) => {
        this.eventDispatcher.dispatch(EventTypes.QUEUE_UPDATE, payload);
      });
    }

    // Subscribe and handle status
    return new Promise((resolve, reject) => {
      channel.subscribe((status) => {
        if (status === 'SUBSCRIBED') {
          console.log(`✅ Subscribed to ${channelName}`);
          resolve(channel);
        } else if (status === 'CHANNEL_ERROR') {
          console.error(`❌ Error subscribing to ${channelName}`);
          reject(new Error(`Failed to subscribe to ${channelName}`));
        }
      });
    });
  }

  // ... rest of the methods (connectStaffChannel, connectConversationChannel, etc.)
  // Keep the existing code for these methods
  async connectStaffChannel(staffId) {
    const channelName = `staff:${staffId}`;
    const channel = this.supabase.channel(channelName);

    // Subscribe to queue updates for this staff member
    channel.on('postgres_changes', {
      event: 'UPDATE',
      schema: 'public',
      table: Tables.MANUAL_REVIEW_QUEUE,
      filter: `assigned_to=eq.${staffId}`,
    }, (payload) => {
      this.eventDispatcher.dispatch(EventTypes.QUEUE_UPDATE, payload);
    });

    // Subscribe to workload updates
    channel.on('postgres_changes', {
      event: 'UPDATE',
      schema: 'public',
      table: Tables.STAFF_WORKLOAD,
      filter: `staff_id=eq.${staffId}`,
    }, (payload) => {
      this.eventDispatcher.dispatch(EventTypes.WORKLOAD_UPDATE, payload);
    });

    // Subscribe to notifications for this staff
    channel.on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: Tables.NOTIFICATIONS,
      filter: `user_id=eq.${staffId}`,
    }, (payload) => {
      this.eventDispatcher.dispatch(EventTypes.NOTIFICATION_INSERT, payload);
    });

    // Presence for staff online status
    this.setupStaffPresence(channel, staffId);

    return new Promise((resolve, reject) => {
      channel.subscribe((status) => {
        if (status === 'SUBSCRIBED') {
          console.log(`✅ Subscribed to ${channelName}`);
          resolve(channel);
        } else if (status === 'CHANNEL_ERROR') {
          reject(new Error(`Failed to subscribe to ${channelName}`));
        }
      });
    });
  }

  async connectConversationChannel(convId) {
    const channelName = `conversation:${convId}`;
    const channel = this.supabase.channel(channelName);

    // Subscribe to messages
    channel.on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: Tables.MESSAGES,
      filter: `conversation_id=eq.${convId}`,
    }, (payload) => {
      this.eventDispatcher.dispatch(EventTypes.MESSAGE_INSERT, payload);
    });

    channel.on('postgres_changes', {
      event: 'UPDATE',
      schema: 'public',
      table: Tables.MESSAGES,
      filter: `conversation_id=eq.${convId}`,
    }, (payload) => {
      this.eventDispatcher.dispatch(EventTypes.MESSAGE_UPDATE, payload);
    });

    // Typing indicator (Broadcast)
    channel.on('broadcast', { event: 'typing' }, (payload) => {
      this.eventDispatcher.dispatch('TYPING_UPDATE', payload);
    });

    // Read receipts (Broadcast)
    channel.on('broadcast', { event: 'read_receipt' }, (payload) => {
      this.eventDispatcher.dispatch('READ_RECEIPT_UPDATE', payload);
    });

    // Presence for conversation participants
    this.setupConversationPresence(channel, convId);

    return new Promise((resolve, reject) => {
      channel.subscribe((status) => {
        if (status === 'SUBSCRIBED') {
          console.log(`✅ Subscribed to ${channelName}`);
          resolve(channel);
        } else if (status === 'CHANNEL_ERROR') {
          reject(new Error(`Failed to subscribe to ${channelName}`));
        }
      });
    });
  }

  // ... rest of the helper methods
  setupStaffPresence(channel, staffId) {
    // Simple presence tracking without external dependency
    const presenceTrack = {
      user_id: staffId,
      status: 'online',
      last_seen: new Date().toISOString(),
    };

    // Track presence
    channel.presence().track(presenceTrack);

    // Log presence changes
    channel.presence().on('sync', () => {
      const state = channel.presence().state();
      // Dispatch presence update
      this.eventDispatcher.dispatch('PRESENCE_UPDATE', {
        staffId,
        online: Object.keys(state),
        timestamp: new Date().toISOString(),
      });
    });
  }

  setupConversationPresence(channel, conversationId) {
    if (!this.user) return;

    const presenceTrack = {
      user_id: this.user.id,
      conversation_id: conversationId,
      status: 'active',
      last_seen: new Date().toISOString(),
    };

    channel.presence().track(presenceTrack);

    channel.presence().on('sync', () => {
      const state = channel.presence().state();
      this.eventDispatcher.dispatch('CONVERSATION_PRESENCE', {
        conversationId,
        participants: state,
      });
    });
  }

  // ... rest of the methods (sendTyping, sendReadReceipt, etc.)
  // Keep existing code

  /**
   * Disconnect all channels
   */
  disconnect() {
    for (const [key, channel] of this.channels) {
      try {
        channel.unsubscribe();
        console.log(`🔌 Unsubscribed from ${key}`);
      } catch (e) {
        console.warn(`Error unsubscribing from ${key}:`, e);
      }
    }
    this.channels.clear();
    this.isConnected = false;
    this.eventDispatcher.dispatch('DISCONNECTED', {});
    console.log('🔌 Realtime disconnected');
  }

  /**
   * Get active conversations for user
   */
  async getActiveConversations() {
    try {
      const { data, error } = await this.supabase
        .from('conversation_participants')
        .select('conversation_id')
        .eq('user_id', this.user.id)
        .eq('is_active', true);

      if (error) {
        console.warn('Could not get active conversations:', error);
        return [];
      }

      return data.map(d => ({ id: d.conversation_id }));
    } catch (error) {
      console.warn('Error getting active conversations:', error);
      return [];
    }
  }

  /**
   * Register an event listener
   */
  on(event, callback) {
    this.eventDispatcher.on(event, callback);
  }

  /**
   * Remove an event listener
   */
  off(event, callback) {
    this.eventDispatcher.off(event, callback);
  }
}

// Event Dispatcher class
class EventDispatcher {
  constructor() {
    this.listeners = new Map();
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
    return () => this.off(event, callback);
  }

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

  clear() {
    this.listeners.clear();
  }
}

// Singleton instance
let instance = null;

export function getRealtimeManager() {
  if (!instance) {
    instance = new RealtimeManager();
  }
  return instance;
}

export default RealtimeManager;
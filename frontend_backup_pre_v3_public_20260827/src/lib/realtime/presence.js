/**
 * Presence Manager
 * Handle user presence across channels
 */

export class PresenceManager {
  constructor(supabase) {
    this.supabase = supabase;
    this.presenceState = {};
    this.conversationPresence = {};
  }

  /**
   * Setup staff presence
   */
  setupStaffPresence(channel, staffId) {
    const presenceTrack = {
      user_id: staffId,
      status: 'online',
      last_seen: new Date().toISOString(),
    };

    // Track presence
    channel.presence().track(presenceTrack);

    // Listen for presence changes
    channel.presence().on('sync', () => {
      const state = channel.presence().state();
      this.presenceState = state;
      
      // Dispatch event
      channel.send({
        type: 'broadcast',
        event: 'presence_update',
        payload: {
          staffId,
          online: Object.keys(state),
          timestamp: new Date().toISOString(),
        },
      });
    });

    // Handle joins
    channel.presence().on('join', ({ key, newPresences }) => {
      console.log(`👤 Staff joined: ${key}`, newPresences);
    });

    // Handle leaves
    channel.presence().on('leave', ({ key, leftPresences }) => {
      console.log(`👤 Staff left: ${key}`, leftPresences);
    });
  }

  /**
   * Setup conversation presence
   */
  setupConversationPresence(channel, conversationId, userId) {
    const presenceTrack = {
      user_id: userId,
      conversation_id: conversationId,
      status: 'active',
      last_seen: new Date().toISOString(),
    };

    // Track presence
    channel.presence().track(presenceTrack);

    // Listen for presence changes
    channel.presence().on('sync', () => {
      const state = channel.presence().state();
      this.conversationPresence[conversationId] = state;
    });

    // Handle joins
    channel.presence().on('join', ({ key, newPresences }) => {
      const event = {
        conversationId,
        userId: key,
        action: 'join',
        timestamp: new Date().toISOString(),
      };
      channel.send({
        type: 'broadcast',
        event: 'participant_join',
        payload: event,
      });
    });

    // Handle leaves
    channel.presence().on('leave', ({ key, leftPresences }) => {
      const event = {
        conversationId,
        userId: key,
        action: 'leave',
        timestamp: new Date().toISOString(),
      };
      channel.send({
        type: 'broadcast',
        event: 'participant_leave',
        payload: event,
      });
    });
  }

  /**
   * Get online staff
   */
  getOnlineStaff() {
    return Object.keys(this.presenceState);
  }

  /**
   * Get conversation participants
   */
  getConversationParticipants(conversationId) {
    return this.conversationPresence[conversationId] || {};
  }

  /**
   * Leave conversation
   */
  leaveConversation(conversationId, userId) {
    const state = this.conversationPresence[conversationId];
    if (state && state[userId]) {
      // Remove presence track
      delete state[userId];
    }
  }
}
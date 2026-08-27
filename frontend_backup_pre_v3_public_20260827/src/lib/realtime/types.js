/**
 * Realtime Type Definitions
 * All types used across the realtime system
 */

// Channel Types
export const ChannelTypes = {
  ORGANIZATION: 'organization',
  STAFF: 'staff',
  CONVERSATION: 'conversation',
  GLOBAL: 'global',
};

// Event Types
export const EventTypes = {
  // Notification events
  NOTIFICATION_INSERT: 'NOTIFICATION_INSERT',
  NOTIFICATION_UPDATE: 'NOTIFICATION_UPDATE',
  
  // Document events
  DOCUMENT_INSERT: 'DOCUMENT_INSERT',
  DOCUMENT_UPDATE: 'DOCUMENT_UPDATE',
  
  // Message events
  MESSAGE_INSERT: 'MESSAGE_INSERT',
  MESSAGE_UPDATE: 'MESSAGE_UPDATE',
  
  // Verification events
  VERIFICATION_INSERT: 'VERIFICATION_INSERT',
  VERIFICATION_UPDATE: 'VERIFICATION_UPDATE',
  
  // Queue events
  QUEUE_INSERT: 'QUEUE_INSERT',
  QUEUE_UPDATE: 'QUEUE_UPDATE',
  
  // Activity feed events
  ACTIVITY_INSERT: 'ACTIVITY_INSERT',
  
  // Workload events
  WORKLOAD_UPDATE: 'WORKLOAD_UPDATE',
  
  // Presence events
  PRESENCE_SYNC: 'PRESENCE_SYNC',
  PRESENCE_JOIN: 'PRESENCE_JOIN',
  PRESENCE_LEAVE: 'PRESENCE_LEAVE',
  
  // Broadcast events
  TYPING_START: 'TYPING_START',
  TYPING_STOP: 'TYPING_STOP',
  READ_RECEIPT: 'READ_RECEIPT',
};

// Table Names
export const Tables = {
  NOTIFICATIONS: 'notifications',
  MESSAGES: 'messages',
  CUSTOMER_DOCUMENTS: 'customer_documents',
  CUSTOMER_VERIFICATIONS: 'customer_verifications',
  MANUAL_REVIEW_QUEUE: 'manual_review_queue',
  STAFF_WORKLOAD: 'staff_workload',
  ACTIVITY_FEED: 'activity_feed',
  CONVERSATIONS: 'conversations',
  CUSTOMER_REVIEW_LOG: 'customer_review_log',
};

// Channel Configuration
export const ChannelConfig = {
  [ChannelTypes.ORGANIZATION]: {
    prefix: 'org',
    events: [
      EventTypes.NOTIFICATION_INSERT,
      EventTypes.DOCUMENT_UPDATE,
      EventTypes.VERIFICATION_UPDATE,
      EventTypes.ACTIVITY_INSERT,
    ],
  },
  [ChannelTypes.STAFF]: {
    prefix: 'staff',
    events: [
      EventTypes.QUEUE_UPDATE,
      EventTypes.WORKLOAD_UPDATE,
    ],
  },
  [ChannelTypes.CONVERSATION]: {
    prefix: 'conversation',
    events: [
      EventTypes.MESSAGE_INSERT,
      EventTypes.MESSAGE_UPDATE,
    ],
  },
};
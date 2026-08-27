/**
 * Channel Utilities
 * Helper functions for channel management
 */

import { ChannelTypes } from './types';

/**
 * Get channel key for Map storage
 */
export function getChannelKey(type, id) {
  return `${type}:${id}`;
}

/**
 * Get channel name for Supabase
 */
export function getChannelName(type, id) {
  const prefixes = {
    [ChannelTypes.ORGANIZATION]: 'org',
    [ChannelTypes.STAFF]: 'staff',
    [ChannelTypes.CONVERSATION]: 'conversation',
    [ChannelTypes.GLOBAL]: 'global',
  };
  return `${prefixes[type]}:${id}`;
}

/**
 * Create channel configuration
 */
export function createChannel(type, id, options = {}) {
  return {
    name: getChannelName(type, id),
    key: getChannelKey(type, id),
    type,
    id,
    options,
  };
}
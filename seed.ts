// supabase/seed/config.ts
/**
 * CarbonTally Seed Configuration
 * 
 * All seeder settings are centralized here for easy tuning.
 * These values control the volume, distribution, and behavior
 * of generated demo data.
 */

export interface SeedConfig {
  // ============================================================
  // ORGANIZATIONS & FACILITIES
  // ============================================================
  
  /** Number of organizations to create */
  ORGANIZATIONS: number;
  
  /** Range [min, max] of facilities per organization */
  FACILITIES_PER_ORG: [number, number];
  
  /** Range [min, max] of members per organization */
  MEMBERS_PER_ORG: [number, number];
  
  /** Range [min, max] of suppliers per organization */
  SUPPLIERS_PER_ORG: [number, number];
  
  /** Range [min, max] of supplier contacts per supplier */
  SUPPLIER_CONTACTS_PER_SUPPLIER: [number, number];
  
  /** Range [min, max] of product categories per organization */
  PRODUCT_CATEGORIES_PER_ORG: [number, number];

  // ============================================================
  // DOCUMENTS & PROCESSING
  // ============================================================
  
  /** Range [min, max] of documents per organization per month */
  DOCUMENTS_PER_MONTH: [number, number];
  
  /** Probability (0-1) that a document is AI-processed */
  AI_PROCESSING_RATE: number;
  
  /** Probability (0-1) that a document requires manual review */
  MANUAL_REVIEW_RATE: number;
  
  /** Probability (0-1) that a document fails QC and needs rework */
  QC_FAILURE_RATE: number;
  
  /** Probability (0-1) that an AI extraction has low confidence */
  LOW_AI_CONFIDENCE_RATE: number;

  // ============================================================
  // REPORTS
  // ============================================================
  
  /** Range [min, max] of reports generated per organization per month */
  REPORTS_PER_MONTH: [number, number];
  
  /** Probability (0-1) that a report is rejected and regenerated */
  REPORT_REJECTION_RATE: number;
  
  /** Probability (0-1) that a report requires validation */
  REPORT_VALIDATION_RATE: number;

  // ============================================================
  // NOTIFICATIONS & MESSAGES
  // ============================================================
  
  /** Range [min, max] of notifications per organization per day */
  NOTIFICATIONS_PER_DAY: [number, number];
  
  /** Range [min, max] of internal messages per user per month */
  MESSAGES_PER_USER_PER_MONTH: [number, number];
  
  /** Range [min, max] of conversations per organization */
  CONVERSATIONS_PER_ORG: [number, number];

  // ============================================================
  // TASKS
  // ============================================================
  
  /** Range [min, max] of tasks per user */
  TASKS_PER_USER: [number, number];
  
  /** Probability (0-1) that a task is overdue */
  OVERDUE_TASK_RATE: number;
  
  /** Probability (0-1) that a task is high priority */
  HIGH_PRIORITY_TASK_RATE: number;

  // ============================================================
  // SUPPORT TICKETS
  // ============================================================
  
  /** Range [min, max] of support tickets per organization */
  SUPPORT_TICKETS_PER_ORG: [number, number];
  
  /** Probability (0-1) that a ticket is escalated */
  TICKET_ESCALATION_RATE: number;
  
  /** Probability (0-1) that a ticket is resolved */
  TICKET_RESOLVED_RATE: number;

  // ============================================================
  // AUDIT LOGS
  // ============================================================
  
  /** Range [min, max] of audit logs per day across all organizations */
  AUDIT_LOGS_PER_DAY: [number, number];

  // ============================================================
  // TIME RANGE
  // ============================================================
  
  /** Start date for generated data (ISO format) */
  START_DATE: string;
  
  /** End date for generated data (ISO format) */
  END_DATE: string;

  // ============================================================
  // BATCHING & PERFORMANCE
  // ============================================================
  
  /** Number of records to insert per batch */
  BATCH_SIZE: number;
  
  /** Whether to show verbose progress output */
  VERBOSE: boolean;
  
  /** Whether to log SQL queries for debugging */
  DEBUG_SQL: boolean;

  // ============================================================
  // RESET & APPEND MODES
  // ============================================================
  
  /** Operation mode: 'reset' (truncate & reseed) or 'append' (add data) */
  MODE: 'reset' | 'append';
  
  /** Tables to preserve when in reset mode (don't truncate) */
  PRESERVE_TABLES: string[];
}

/**
 * Default configuration optimized for a realistic 12-month demo
 * with 100 organizations generating meaningful activity.
 */
export const defaultConfig: SeedConfig = {
  // Organizations & Facilities
  ORGANIZATIONS: 100,
  FACILITIES_PER_ORG: [2, 8],
  MEMBERS_PER_ORG: [3, 15],
  SUPPLIERS_PER_ORG: [20, 120],
  SUPPLIER_CONTACTS_PER_SUPPLIER: [1, 4],
  PRODUCT_CATEGORIES_PER_ORG: [3, 8],

  // Documents & Processing
  DOCUMENTS_PER_MONTH: [5, 30],
  AI_PROCESSING_RATE: 0.75,
  MANUAL_REVIEW_RATE: 0.20,
  QC_FAILURE_RATE: 0.10,
  LOW_AI_CONFIDENCE_RATE: 0.08,

  // Reports
  REPORTS_PER_MONTH: [1, 4],
  REPORT_REJECTION_RATE: 0.05,
  REPORT_VALIDATION_RATE: 0.30,

  // Notifications & Messages
  NOTIFICATIONS_PER_DAY: [2, 10],
  MESSAGES_PER_USER_PER_MONTH: [3, 12],
  CONVERSATIONS_PER_ORG: [5, 25],

  // Tasks
  TASKS_PER_USER: [3, 12],
  OVERDUE_TASK_RATE: 0.15,
  HIGH_PRIORITY_TASK_RATE: 0.20,

  // Support Tickets
  SUPPORT_TICKETS_PER_ORG: [2, 8],
  TICKET_ESCALATION_RATE: 0.15,
  TICKET_RESOLVED_RATE: 0.80,

  // Audit Logs
  AUDIT_LOGS_PER_DAY: [5, 25],

  // Time Range
  START_DATE: '2025-08-01',
  END_DATE: '2026-08-01',

  // Batching & Performance
  BATCH_SIZE: 500,
  VERBOSE: true,
  DEBUG_SQL: false,

  // Reset & Append
  MODE: 'reset',
  PRESERVE_TABLES: [
    'users',
    'roles',
    'staff_roles',
    'document_types',
    'document_type_categories',
    'supplier_categories',
    'activity_categories',
    'units',
    'defra_conversion_factors',
    'system_settings',
    'notification_templates',
    'email_templates',
    'glossary',
    'business_hours',
    'sla_definitions',
    'qc_checklists',
  ],
};

/**
 * Development configuration - smaller dataset for faster seeding
 */
export const devConfig: SeedConfig = {
  ...defaultConfig,
  ORGANIZATIONS: 10,
  FACILITIES_PER_ORG: [1, 4],
  MEMBERS_PER_ORG: [2, 6],
  SUPPLIERS_PER_ORG: [5, 20],
  DOCUMENTS_PER_MONTH: [2, 8],
  REPORTS_PER_MONTH: [1, 2],
  NOTIFICATIONS_PER_DAY: [1, 3],
  CONVERSATIONS_PER_ORG: [1, 5],
  SUPPORT_TICKETS_PER_ORG: [1, 3],
  AUDIT_LOGS_PER_DAY: [2, 5],
  BATCH_SIZE: 100,
  VERBOSE: true,
};

/**
 * Production demo configuration - large dataset for realistic demos
 */
export const demoConfig: SeedConfig = {
  ...defaultConfig,
  ORGANIZATIONS: 250,
  FACILITIES_PER_ORG: [3, 12],
  MEMBERS_PER_ORG: [5, 25],
  SUPPLIERS_PER_ORG: [30, 200],
  DOCUMENTS_PER_MONTH: [10, 50],
  REPORTS_PER_MONTH: [2, 6],
  NOTIFICATIONS_PER_DAY: [5, 20],
  CONVERSATIONS_PER_ORG: [10, 40],
  SUPPORT_TICKETS_PER_ORG: [5, 15],
  BATCH_SIZE: 1000,
};

/**
 * Load configuration from environment variables or use defaults
 */
export function loadConfig(): SeedConfig {
  const env = process.env.NODE_ENV || 'development';
  const mode = process.env.SEED_MODE || 'reset';
  const configName = process.env.SEED_CONFIG || 'default';

  let config: SeedConfig;

  switch (configName) {
    case 'dev':
      config = { ...devConfig };
      break;
    case 'demo':
      config = { ...demoConfig };
      break;
    default:
      config = { ...defaultConfig };
      break;
  }

  // Override with environment variables
  if (process.env.SEED_ORGANIZATIONS) {
    config.ORGANIZATIONS = parseInt(process.env.SEED_ORGANIZATIONS, 10);
  }

  if (process.env.SEED_START_DATE) {
    config.START_DATE = process.env.SEED_START_DATE;
  }

  if (process.env.SEED_END_DATE) {
    config.END_DATE = process.env.SEED_END_DATE;
  }

  if (process.env.SEED_MODE) {
    config.MODE = process.env.SEED_MODE as 'reset' | 'append';
  }

  if (process.env.SEED_BATCH_SIZE) {
    config.BATCH_SIZE = parseInt(process.env.SEED_BATCH_SIZE, 10);
  }

  if (process.env.SEED_VERBOSE) {
    config.VERBOSE = process.env.SEED_VERBOSE === 'true';
  }

  // Env takes precedence over config mode
  config.MODE = mode as 'reset' | 'append';

  return config;
}

// Export singleton configuration
export const config = loadConfig();

export default config;
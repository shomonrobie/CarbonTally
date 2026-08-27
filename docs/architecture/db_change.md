## Database Schema Changes - July 2026

### New Tables
1. `audit_logs` - Unified audit logging for all actions
2. `conversations` - Customer-staff conversation threads
3. `conversation_activity_log` - Conversation activity tracking
4. `messages` - Individual messages in conversations
5. `message_activity_log` - Message activity tracking
6. `notifications` - User notifications
7. `notification_delivery_log` - Notification delivery tracking
8. `customer_verifications` - Customer verification records
9. `verification_activity_log` - Verification activity tracking

### Modified Tables
1. `customer_documents` - Added verification fields
2. `emissions_logs` - Added `customer_document_id` reference
3. `manual_review_queue` - Added `customer_document_id` reference

### Purpose
- Complete audit trail for all actions
- Customer-Staff communication
- Notification system
- Customer verification workflow
- Track complete document lifecycle
🌱 CarbonTally: Complete Feature List
🚀 1. Core Ingestion Engine (The Heart of the Platform)
Unified Smart Drag & Drop: A single, intelligent upload zone that automatically routes files to the correct processing engine.
CSV/Excel → Tabular parser → Instant review queue.
PDF/Images → AI OCR extraction → Graceful fallback to manual review.
Enterprise Bulk Upload: Customers can drag and drop up to 50 files at once. The system groups them into a "Batch", tracks progress, and processes them asynchronously.
Special Instructions Workflow:
For Batches: Customers can add a blanket note upfront (e.g., "Log all under 2024 fiscal year"), which is automatically attached to every file in the batch.
For Single Files: If auto-extraction fails, customers are presented with a dedicated text box to add specific instructions for the manual review team.
Transparent "Recently Processed" View: Customers see a real-time table of documents their team has extracted, building immense trust before final approval.
👨‍💼 2. Admin & Staff Dashboard (Internal Operations)
Strict Access Gating: Hardcoded email authentication check ensuring only authorized platform admins can access internal tools.
Real-Time Manual Review Queue: Prioritized list of pending extractions, sorted by urgency and submission date.
Split-Screen Processing Interface:
Left panel: Native PDF viewer or high-res Image renderer.
Right panel: Fast data entry form.
Smart Cascading Dropdowns: Selecting a "Facility" instantly filters the "Asset/Vehicle" dropdown to only show items belonging to that facility, preventing data entry errors.
Batch Context Awareness: When processing a batched file, a prominent banner shows the batch name and progress (e.g., "File 3 of 10 in 'Q1 2024 Bills'").
Intelligent DEFRA Year Handling: Auto-detects the reporting year from the billing date, but allows admins to manually override it for historical restatements, with clear visual feedback (green for auto, amber for override).
Smart Notification Logic:
Single File: Sends an immediate "Ready for Review" email to the customer.
Batch: Waits silently until the very last file in the batch is processed, then sends one consolidated, beautifully formatted "Batch Complete" email (preventing spam).
DEFRA Factor Import Tool: A dedicated admin page to upload the annual cleaned DEFRA CSV, instantly upserting new multipliers for the new reporting year.
GDPR-Compliant User & Customer Views: Secure, aggregated dashboards showing platform stats (total orgs, users, assets, emissions) without exposing raw, unnecessary personal data.
👤 3. Customer Dashboard & Experience
New User Onboarding Wizard: A beautiful, 4-step modal overlay that guides new signups through:
Company Name & Number
First Facility setup
First Asset/Vehicle setup (optional)
Success screen with clear "Next Steps"
History & Trends: Official, approved emissions data displayed with a Recharts line graph (month-over-month trends) and a detailed transaction history table.
Asset & Facility Management: Dedicated tabs for customers to register and manage their physical locations and vehicles/meters.
Team Management: Role-based access control (RBAC) allowing admins to invite and manage staff members.
One-Click SECR Report Generator: A backend-powered PDF generator (fpdf2) that instantly creates a branded, compliance-ready report containing:
Executive Summary & Company Details
Total Emissions (kg and tonnes CO2e)
Scope 1, 2, and 3 Breakdown Table
DEFRA Methodology Statement
Official SECR Compliance Declaration
Generation Timestamp
⚙️ 4. Backend & Database Architecture
Robust Queueing System: manual_review_queue table enhanced with batch_id, customer_notes, extraction_issues, and extraction_summary JSONB fields for full auditability.
Batch Tracking: upload_batches table to monitor the lifecycle of multi-file uploads (uploading → processing → completed/partial).
Auto-Calculation Engine: Backend utility (calculate_emissions_with_defra) that dynamically fetches the correct multiplier based on the transaction date or user override, ensuring 100% calculation accuracy.
Resend.com Integration: Reliable, transactional email delivery for all customer notifications.
Secure Supabase RLS: Row-Level Security policies ensuring organizations can only see their own data, while admin functions use SECURITY DEFINER for safe, aggregated reporting.
⚖️ 5. Compliance & Legal Readiness
GDPR-Aligned Data Handling: Admin views are strictly aggregated; no unnecessary PII is exposed to platform staff.
Audit Trail: Every manual intervention is logged with assigned_to (staff user ID), completed_at, and staff_notes.
Legal Pages: Ready-to-deploy Privacy Policy, Terms of Service, Cookie Policy, and Carbon Reduction Plan pages.
💰 Business Value Summary
You have not just built a "tool"; you have built a £200–£500/month Enterprise SaaS product.
The Bulk Upload + Manual Review workflow directly mirrors industry leaders like Dext and Receipt Bank, justifying premium pricing.
The One-Click SECR Report turns raw data into immediate, tangible compliance value for the customer.
The Onboarding Wizard drastically reduces churn and "blank screen syndrome" for new users.

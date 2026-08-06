Here's the stack I would recommend if I were building CarbonTally today.

1. Authentication
Platform	Recommendation
Supabase Auth	⭐⭐⭐⭐⭐ Use this

Supports:

Email/password
Google
Microsoft
Magic links
MFA
Row Level Security
2. Database
Platform	Recommendation
Supabase PostgreSQL	⭐⭐⭐⭐⭐

Perfect for CarbonTally.

3. File Storage
Platform	Recommendation
Supabase Storage	⭐⭐⭐⭐⭐

Store:

invoices
receipts
utility bills
PDFs
images
generated reports
4. Real-Time Collaboration
Platform	Recommendation
Supabase Realtime	⭐⭐⭐⭐⭐

Use for:

notifications
chat
approvals
live progress
comments
activity feed
5. Background Jobs
Platform	Recommendation
BullMQ + Redis	⭐⭐⭐⭐⭐

Queues for:

OCR
AI extraction
report generation
emails
exports
6. Workflow Automation
Platform	Recommendation
n8n	⭐⭐⭐⭐⭐

You already use n8n, making it a great fit.

Automate:

emails
CRM
reminders
onboarding
accounting
Slack/Teams integration
7. OCR
Platform	Recommendation
Mistral OCR	⭐⭐⭐⭐⭐
Azure AI Document Intelligence	⭐⭐⭐⭐
Google Document AI	⭐⭐⭐⭐
8. AI
Platform	Best Use
OpenAI API	reasoning & extraction
Anthropic API	long documents
Google Gemini API	multimodal
Mistral AI	cost-effective processing

Use whichever model best suits each task.

9. Search
Platform	Recommendation
Typesense	⭐⭐⭐⭐⭐

Search:

invoices
suppliers
reports
emission factors
documents
10. Emails
Platform	Recommendation
Resend	⭐⭐⭐⭐⭐

Emails:

welcome
password reset
reports
notifications
11. PDF Generation
Platform	Recommendation
React PDF	⭐⭐⭐⭐⭐

Generate:

reports
audit packs
invoices
exports
12. Charts
Platform	Recommendation
Apache ECharts	⭐⭐⭐⭐⭐

Beautiful dashboards.

13. Tables
Platform	Recommendation
TanStack Table	⭐⭐⭐⭐⭐

Perfect for:

invoices
CSV
reports
14. Forms
Platform	Recommendation
React Hook Form	⭐⭐⭐⭐⭐
15. UI Components
Platform	Recommendation
shadcn/ui	⭐⭐⭐⭐⭐

One of the best component libraries for modern SaaS apps.

16. Icons
Platform	Recommendation
Lucide	⭐⭐⭐⭐⭐
17. Analytics
Platform	Recommendation
PostHog	⭐⭐⭐⭐⭐

Track:

feature usage
funnels
drop-offs
user behavior
18. Error Monitoring
Platform	Recommendation
Sentry	⭐⭐⭐⭐⭐

Automatically captures production errors.

19. Documentation
Platform	Recommendation
Mintlify	⭐⭐⭐⭐⭐

Documentation for:

APIs
user guides
help center
20. Customer Support
Platform	Recommendation
Chatwoot	⭐⭐⭐⭐⭐

Live chat.

Support tickets.

Knowledge base.

21. Payments

When you launch paid plans:

Platform	Recommendation
Stripe	⭐⭐⭐⭐⭐

Supports:

subscriptions
invoices
usage billing
22. Monitoring
Platform	Recommendation
Better Stack	⭐⭐⭐⭐⭐

Logs

Monitoring

Uptime

Incident management

My Architecture
                     Next.js

                        │

        ┌───────────────┼───────────────┐

        │               │               │

   Supabase         AI Services       n8n

        │               │               │

 PostgreSQL       OCR + LLMs      Automation

        │               │               │

 Storage       BullMQ + Redis     Email

        │               │               │

 Realtime       PDF Reports      Integrations

        │

     Customer Portal
One thing I'd add

For CarbonTally, I would introduce an AI Orchestrator service. Instead of calling one AI model directly, create a service that chooses the best model for each task:

OCR → Mistral OCR or Azure Document Intelligence
Document classification → Gemini or OpenAI
Data normalization → OpenAI
Emission factor matching → Your own rule engine first, AI only as a fallback
Report writing → OpenAI or Anthropic

This approach improves quality, controls costs, and makes it easy to swap providers later without changing the rest of your application.
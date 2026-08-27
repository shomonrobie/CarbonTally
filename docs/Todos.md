# CarbonTally - TODO & Implementation Plan

## 🎯 Current Status
- **Version**: v1.0 (Single Organization per User)
- **Status**: In Development
- **Backend**: FastAPI with Supabase
- **Frontend**: React with Realtime features

---

## ✅ COMPLETED

### Backend API Endpoints Fixed
- [x] Added `/api/organizations/members/user/{user_id}` endpoint
- [x] Fixed organization retrieval for authenticated users
- [x] Fixed CORS configuration
- [x] Added proper error handling for organization endpoints

### Frontend API Integration
- [x] Updated `fetchWithAuth` to use `/api` prefix
- [x] Fixed all API endpoints in App.js
- [x] Updated `fetchOrganization` to use new endpoint
- [x] Fixed `createOrganizationFromMetadata` endpoint
- [x] Added proper error handling for network failures

### Chat Widget Implementation
- [x] Created floating chat widget
- [x] Integrated with Supabase Realtime
- [x] Added unread message counts
- [x] Staff/User communication setup

### Asset Manager Fixed
- [x] Added organization ID to all API calls
- [x] Fixed facilities endpoint
- [x] Fixed assets endpoint
- [x] Added proper error handling

### Upload Manager Fixed
- [x] Fixed facilities endpoint with org ID
- [x] Fixed assets endpoint with org ID
- [x] Fixed bulk upload endpoint
- [x] Added document status polling

### Manual Entry Standalone Fixed
- [x] Fixed facilities endpoint with org ID
- [x] Fixed assets endpoint with org ID
- [x] Added asset suggestions
- [x] Fixed DEFRA factors endpoint

### Reference Data Context
- [x] Created global reference data provider
- [x] Added fuel types caching
- [x] Added units caching
- [x] Added facilities caching
- [x] 1-hour cache expiration

---

## 🔄 IN PROGRESS

### Backend Development
- [ ] Test all API endpoints with real data
- [ ] Add proper validation for all endpoints
- [ ] Add rate limiting for public endpoints
- [ ] Add request logging middleware
- [ ] Add health check endpoint

### Frontend Development
- [ ] Test all API integrations
- [ ] Fix remaining 404 errors
- [ ] Add loading states for all API calls
- [ ] Add retry logic for failed API calls
- [ ] Improve error messaging for users

### Testing
- [ ] Write unit tests for critical functions
- [ ] Test all API endpoints
- [ ] Test error scenarios
- [ ] Test edge cases
- [ ] Performance testing

---

## 📋 PENDING / TO DO

### 1. Complete API Integration
- [ ] Fix `/api/emissions/stats` endpoint or replace with `/api/organizations/{org_id}/assets/stats`
- [ ] Fix `/api/emissions/history` endpoint or replace with `/api/organizations/{org_id}/emissions-data`
- [ ] Fix `/api/documents/stats` endpoint
- [ ] Fix `/api/upload-csv` endpoint (remove /api? keep as is)
- [ ] Fix `/api/generate-enhanced-report` and `/api/generate-sustainability-report` endpoints

### 2. Data Flow Optimization
- [ ] Use ReferenceDataContext for all components
- [ ] Centralize API calls in a service layer
- [ ] Add request/response interceptors
- [ ] Implement optimistic updates
- [ ] Add offline support with local caching

### 3. Chat System
- [ ] Fix `toast.info` -> `toast.success` in RealtimeContext
- [ ] Add typing indicators
- [ ] Add read receipts
- [ ] Add file attachments
- [ ] Add message search
- [ ] Add conversation archive

### 4. Performance
- [ ] Add React.memo for expensive components
- [ ] Lazy load routes
- [ ] Optimize bundle size
- [ ] Add Virtual Scroll for large lists
- [ ] Implement image optimization
- [ ] Add service worker for offline support

### 5. Error Handling
- [ ] Global error boundary
- [ ] Custom error pages (404, 500, etc.)
- [ ] Retry logic with exponential backoff
- [ ] Offline mode indicator
- [ ] Connection status monitoring
- [ ] Toast notifications for all API errors

### 6. UI/UX Improvements
- [ ] Mobile responsive fixes
- [ ] Loading skeletons for all list views
- [ ] Animated transitions
- [ ] Keyboard shortcuts
- [ ] Dark mode support
- [ ] Accessibility (WCAG 2.1 AA)

---

## 🚀 FUTURE FEATURES (Phase 2)

### Multi-Organization Support
- [ ] Design multi-org data model
- [ ] Add organization switcher
- [ ] Add organization invitation system
- [ ] Add organization cloning
- [ ] Add organization archiving
- [ ] Support for consulting firms
  - [ ] Client management dashboard
  - [ ] Cross-client reporting
  - [ ] Consolidated emissions reports
  - [ ] Client-specific branding

### Advanced Reporting
- [ ] Custom report builder
- [ ] Scheduled reports
- [ ] PDF report customization
- [ ] Interactive dashboards
- [ ] Benchmarking against industry peers
- [ ] Export to XLSX/CSV/PDF

### Advanced Analytics
- [ ] AI-powered insights
- [ ] Anomaly detection
- [ ] Predictive analytics
- [ ] Scenario modeling
- [ ] Target tracking
- [ ] Carbon credit calculations
- [ ] Supplier emissions tracking

### Integration
- [ ] API for third-party integrations
- [ ] Webhooks
- [ ] Zapier/IFTTT integration
- [ ] Accounting software integration (Xero, QuickBooks)
- [ ] Energy management systems integration
- [ ] IoT sensor integration

### Compliance
- [ ] SECR report generation (enhanced)
- [ ] CSRD compliance
- [ ] ISSB compliance
- [ ] TCFD compliance
- [ ] EU Taxonomy alignment
- [ ] Audit trail
- [ ] Digital signatures

### User Experience
- [ ] White-labeling
- [ ] Custom branding
- [ ] Multi-language support
- [ ] Time zone support
- [ ] User preferences
- [ ] Keyboard shortcuts
- [ ] Mobile app (React Native)
- [ ] Desktop app (Electron)

---

## 🐛 KNOWN ISSUES & BUGS

### API Issues
1. `GET /api/organizations/members/{user_id}` - ❌ 405 Method Not Allowed (FIXED with new endpoint)
2. `GET /api/emissions/stats` - ❌ 404 Not Found
3. `GET /api/emissions/history` - ❌ 404 Not Found
4. `GET /api/documents/stats` - ❌ 404 Not Found
5. `GET /api/upload-csv` - ❌ Need to verify endpoint
6. `toast.info` error in RealtimeContext - ❌ Need to fix

### Frontend Issues
1. Chat widget not loading - 🔄 In progress
2. Assets/Facilities not displaying - 🔄 In progress
3. Document stats not loading - 🔄 In progress
4. Upload manager API calls failing - 🔄 In progress

---

## 📊 ENDPOINT REFERENCE

### Organization Endpoints (✅ Verified)
| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/api/organizations/members/user/{user_id}` | GET | ✅ Working | New endpoint |
| `/api/organizations` | POST | ✅ Working | Create org |
| `/api/organizations/{org_id}` | GET | ✅ Working | Get org |
| `/api/organizations/{org_id}/assets` | GET | ✅ Working | Get assets |
| `/api/organizations/{org_id}/facilities` | GET | ✅ Working | Get facilities |
| `/api/organizations/{org_id}/assets/stats` | GET | ⚠️ Test | Asset stats |
| `/api/organizations/{org_id}/facilities/stats` | GET | ⚠️ Test | Facility stats |

### Reference Endpoints (✅ Verified)
| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/api/reference/fuel-types` | GET | ✅ Working | Fuel types |
| `/api/reference/units` | GET | ✅ Working | Units |

### Action Endpoints (⚠️ Need Verification)
| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/api/upload-csv` | POST | ⚠️ Verify | CSV upload |
| `/api/emissions` | POST | ⚠️ Verify | Save emissions |
| `/api/defra-factors/{year}` | GET | ⚠️ Verify | Get factors |
| `/api/documents/stats` | GET | ⚠️ Verify | Doc stats |
| `/api/generate-enhanced-report` | POST | ⚠️ Verify | Report gen |

---

## 💡 ARCHITECTURE DECISIONS

### Current State
- **Single Organization**: Each user belongs to one organization
- **Supabase Direct**: Some queries bypass API (to be migrated)
- **Real-time**: Enabled via Supabase realtime subscriptions
- **Caching**: Reference data cached for 1 hour

### Future State (Phase 2)
- **Multi-Organization**: Users can belong to multiple orgs
- **API-First**: All data access through API
- **Micro-frontends**: Split app into smaller chunks
- **GraphQL**: Consider for complex queries

---

## 📝 NOTES

### Code Organization
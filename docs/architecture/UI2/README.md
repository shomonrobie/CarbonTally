markdown
# CarbonTally UI Demo

> A static HTML/CSS/JS demonstration of the CarbonTally carbon emissions management platform UI/UX.

## 🎯 Purpose

This is a **UI/UX demonstration** of CarbonTally, showcasing the complete user interface and user experience of the platform. It uses static HTML, CSS, and JavaScript with mock data to simulate the real application.

**This is NOT the production application.** The actual CarbonTally app is built with:
- **Frontend:** React
- **Backend:** Python (Django/Flask)
- **Database:** PostgreSQL

This demo is intended for:
- 🎨 **Design Review** - Stakeholder approval of UI/UX
- 📊 **User Testing** - User feedback on workflows
- 📋 **Client Presentations** - Showcase features without backend setup
- 🔧 **Frontend Development** - HTML/CSS/JS foundation for React conversion

## ✨ Features

### Core Modules
- 📊 **Dashboard** - KPI overview with real-time stats
- 📁 **Document Management** - Upload, view, and manage documents
- 📤 **Upload Data** - Single and batch file uploads
- 📋 **Validation Queue** - Review and validate documents
- 📈 **Emissions Reports** - Generate and view emissions reports
- 🔑 **Roles & Permissions** - Role-based access control
- 👥 **Team Management** - Manage team members
- ⚙️ **Settings** - Organization preferences

### UI/UX Highlights
- 🎨 **9 Themes** - Forest, Emerald, Navy, Slate, Purple, Rose, etc.
- 📱 **Responsive Design** - Mobile, tablet, and desktop ready
- 🔍 **Global Search** - Search across all modules
- 💬 **Toast Notifications** - User feedback system
- 🎯 **Collapsible Sidebar** - Space-efficient navigation

## 🚀 Getting Started

### Prerequisites
- Any modern web browser (Chrome, Firefox, Safari, Edge)
- Local web server (optional - works with `file://` protocol)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/carbon-tally-ui-demo.git
   cd carbon-tally-ui-demo
Open the application

Option A: Double-click index.html in your file explorer

Option B: Run a local server

bash
# Using Python
python -m http.server 8000

# Using Node.js
npx serve

# Using VS Code Live Server extension
Login (mock authentication)

Email: any valid email

Role: Select Admin, Manager, Analyst, Staff, or Viewer

📁 Project Structure
text
carbon-tally-ui-demo/
├── index.html              # Main SPA entry point
├── css/                    # All CSS files
│   ├── dashboard.css
│   ├── batch_management.css
│   ├── document_man.css
│   ├── uploads_man.css
│   ├── manual_review_queue.css
│   ├── emissions_reports.css
│   ├── roles_permissions.css
│   └── ...
├── js/                     # All JavaScript files
│   ├── dashboard.js        # SPA engine & shared functions
│   ├── batch_management.js
│   ├── document_man.js
│   ├── uploads_man.js
│   ├── manual_review_queue.js
│   ├── emissions_reports.js
│   └── ...
├── modules/               # Individual module HTML
│   ├── dashboard_content.html
│   ├── batch_management.html
│   ├── document_man.html
│   ├── uploads_man.html
│   └── ...
└── README.md
🧪 Demo Credentials
Role	Access
Admin	Full access to all modules
Manager	Management + reporting access
Analyst	Data analysis + reporting
Staff	Basic operational access
Viewer	Read-only access
🛠️ Technology Stack
HTML5 - Semantic markup

CSS3 - Custom properties (CSS variables), Grid, Flexbox

JavaScript (ES6) - Vanilla JS, no frameworks

Local Storage - Theme preferences, sidebar state

📊 Mock Data
The demo includes comprehensive mock data:

15+ documents

20+ facility records

15+ report entries

12+ queue items

16+ permission definitions

7+ user roles

🎨 Theme System
Theme	Color	Style
Forest	🌿 Green	Professional & sustainable
Emerald	💎 Green	Bold & vibrant
Navy	🌊 Blue	Trustworthy & financial
Slate	⚪ Grey	Clean & data-focused
Purple	🟣 Purple	Creative & premium
Rose	🌹 Rose	Warm & distinctive
🔄 Navigation
Sidebar: Collapsible navigation with grouped sections

Search: Global module search (Ctrl+F)

Themes: Cycle themes with arrow keys

Keyboard Shortcuts:

Ctrl+F - Focus search

Ctrl+R - Refresh current module

←/→ - Cycle themes

📝 License
This is a proprietary UI demo for CarbonTally. All rights reserved.

🤝 Contributing
This is a demonstration UI. For the actual CarbonTally application development, please refer to the main repository.

📧 Contact
Website: carbontally.com

Email: demo@carbontally.com

Built with ❤️ for CarbonTally
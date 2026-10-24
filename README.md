# 🎓 UniBudget — Smart Student Budget Tracker

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Framework: Starlette](https://img.shields.io/badge/framework-Starlette-indigo.svg)](https://www.starlette.io/)
[![Server: Uvicorn](https://img.shields.io/badge/server-Uvicorn-green.svg)](https://www.uvicorn.org/)
[![Database: SQLite](https://img.shields.io/badge/database-SQLite-lightgrey.svg)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)

> **UniBudget** is a full-featured, responsive personal finance and budget tracker engineered specifically for university and college students. It helps students budget tuition, textbooks, dorm rent, campus meals, transit, and daily allowances with intelligent pacing metrics and impulse-buying reality checks.

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Screenshots](#-screenshots)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Application](#running-the-application)
- [Demo Credentials](#-demo-credentials)
- [Running Automated Tests](#-running-automated-tests)
- [API Overview](#-api-overview)
- [Future Improvements](#-future-improvements)
- [License](#-license)

---

## 💡 Overview

Managing money in college is uniquely challenging: irregular semester expenses (tuition, textbook bundles, dorm deposits) collide with strict daily spending limits. Most generic finance apps fail to account for student realities like campus dining plans, part-time wages, and transit subsidies.

**UniBudget** bridges this gap by combining essential budget tracking with student-tailored metrics:
- **Daily Safe Spending Limit**: Dynamically calculates `Remaining Balance / Days Left in Month` so you know your exact safe daily ceiling without running out before finals.
- **Spending Pacing Intelligence**: Automatically compares spend velocity against calendar progress, warning you when your burn rate is too fast.
- **"Can I Afford It?" Reality Check**: Translates impulse purchases into hours of campus part-time work and days of daily living allowance.

---

## ✨ Key Features

- **🔐 Student Authentication & Profiles**
  - Secure registration and login with salted SHA-256 password hashing and token-based sessions.
  - Multi-user data isolation.
  - Profile customization: college/university name, academic major, monthly budget limit, preferred currency symbol (`$`, `€`, `£`, `₹`, `C$`, `A$`), and part-time hourly wage.
  - **1-Click Demo Login** for instant portfolio evaluation with pre-seeded data.

- **📊 Comprehensive Financial Dashboard**
  - **Pacing & Health Status Banner**: Color-coded real-time feedback (On Track, Caution, Danger Zone, Exceeded).
  - **4 Stat Summary Cards**: Total Monthly Budget, Total Spent, Remaining Balance, and Recommended Safe Daily Ceiling.
  - **Month-by-Month Navigation**: Historical review and tracking across past and current academic terms.

- **📈 Visual Analytics & Charts (Chart.js)**
  - **Spending by Category (Doughnut Chart)**: Visual breakdown of dorm housing, textbooks, cafeteria, groceries, tech, and transit.
  - **Daily Spending Velocity (Bar Chart)**: Day-by-day expense timeline highlighting spending spikes.
  - **Budget Cap vs. Actual Spent (Horizontal Bar Chart)**: Direct comparison of category caps against actual outlays.
  - **Payment Methods Distribution (Pie Chart)**: Breakdown across Campus ID Cards, Debit Cards, Cash, Credit Cards, and Digital Wallets.

- **🏷️ College-Tailored Expense Categories**
  - Pre-configured with typical student categories: 🏠 Rent & Dorm, 📚 Textbooks & Supplies, 🍎 Groceries, ☕ Campus Dining, 🚌 Transit, 💻 Tech Subscriptions, 🎮 Entertainment, 🏋️ Health & Fitness, and 🦺 Emergency.
  - Visual progress bars showing percentage of category cap utilized.
  - Full CRUD support for custom student categories with custom emoji icons, colors, and spending limits.

- **🎯 "Can I Afford It?" Reality Check Calculator**
  - Instant pre-purchase evaluation tool.
  - Calculates how many hours of campus part-time work (\$16/hr) the item represents.
  - Calculates how many days of daily allowance it consumes, providing a clear verdict (✅ Green Light, 🤔 Moderate Spend, ⚠️ High Impact, 🚨 Budget Breaker).

- **💸 Transaction Management & CSV Export**
  - Add, edit, and delete transactions with category, payment method, date, and notes.
  - Instant search filtering by title/notes and category.
  - Sorting by Newest, Oldest, Highest Amount, and Lowest Amount.
  - **📥 Export to CSV**: One-click download of filtered or full-month financial records.

- **🌓 Dark Mode & Responsive Design**
  - Pure CSS theme engine supporting both Light and Dark modes with automatic persistence in `localStorage`.
  - Fully responsive layout optimized for mobile screens, tablets, and desktop workstations.

---

## 📸 Screenshots

> *Placeholder: Add screenshots of the live application below after hosting or cloning.*

| Light Mode Dashboard | Dark Mode Dashboard |
| :---: | :---: |
| ![Light Mode Dashboard](https://via.placeholder.com/600x340.png?text=UniBudget+Light+Mode+Dashboard) | ![Dark Mode Dashboard](https://via.placeholder.com/600x340.png?text=UniBudget+Dark+Mode+Dashboard) |

| Interactive Charts & Categories | "Can I Afford It?" Calculator |
| :---: | :---: |
| ![Charts and Categories](https://via.placeholder.com/600x340.png?text=Category+Charts+%26+Budgets) | ![Affordability Calculator](https://via.placeholder.com/600x340.png?text=Can+I+Afford+It+Modal) |

---

## 🛠️ Tech Stack

### Backend
- **Language**: Python 3.10+
- **Framework**: [Starlette](https://www.starlette.io/) (High-performance ASGI framework)
- **ASGI Server**: [Uvicorn](https://www.uvicorn.org/)
- **Database**: SQLite3 (Zero-configuration, persistent relational storage)
- **Security**: Salted SHA-256 password hashing, token-based session authentication

### Frontend
- **Interface**: HTML5 Semantic markup, Modern CSS3 with Custom Properties (variables)
- **Design System**: Glassmorphic cards, fluid typography, dark/light theme switching
- **Logic**: Vanilla ES6+ JavaScript (zero build step or heavy dependencies required)
- **Data Visualization**: [Chart.js 4.4](https://www.chartjs.org/) (bundled locally for 100% offline capability)

### Testing
- **Test Runner**: Python standard `unittest` with `starlette.testclient.TestClient` / `httpx`

---

## 📂 Project Structure

```
student-budget-tracker/
├── app.py                     # Starlette ASGI application, REST API endpoints & static routing
├── database.py                # Database connection, schemas, migrations, seed data & queries
├── requirements.txt           # Python application and testing dependencies
├── run.bat                    # 1-Click launcher script for Windows
├── test_app.py                # End-to-end integration and API test suite
├── .gitignore                 # Git ignore rules for Python, virtual environments, and SQLite
├── LICENSE                    # MIT open-source license
├── README.md                  # Comprehensive project documentation
└── static/
    ├── index.html             # Single-Page Application interface
    ├── css/
    │   └── styles.css         # Responsive styling, design tokens, dark/light themes
    └── js/
        ├── app.js             # Core frontend controller, state management, modal handlers
        ├── charts.js          # Chart.js visualization configurations & lifecycle
        └── chart.min.js       # Bundled Chart.js library (offline-ready)
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher installed on your machine.
- Git installed on your system.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/student-budget-tracker.git
   cd student-budget-tracker
   ```

2. **Create and activate a virtual environment (recommended):**
   - **macOS / Linux:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - **Windows:**
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

1. **Start the ASGI server:**
   ```bash
   python app.py
   ```
   *Or on Windows, simply double-click `run.bat`.*

2. **Open in your browser:**
   ```
   http://127.0.0.1:8000
   ```

The database (`student_budget.db`) will be automatically initialized and seeded on first run!

---

## 🔑 Demo Credentials

To evaluate the application immediately without manually filling out forms:

- Click the **"⚡ One-Click Demo Student Login"** button on the sign-in screen, **OR**
- Log in manually using the pre-seeded demo student credentials:
  - **Email:** `alex@student.edu`
  - **Password:** `student123`
  - *Profile:* Alex Rivers — Sophomore Computer Science student at Metropolis University

You can reset the demo data back to its original state anytime via **Profile Settings -> Reset Data**.

---

## 🧪 Running Automated Tests

UniBudget includes an automated integration test suite verifying authentication, profile management, expense CRUD, category caps, dashboard pacing summaries, the affordability calculator, and CSV export.

To execute the test suite:

```bash
python -X utf8 test_app.py
```

Expected output:
```text
[PASS] 1. Index page served successfully (200 OK)
[PASS] 2. Demo student login: Alex Rivers (Metropolis University)
[PASS] 3. Dashboard summary: Budget $1200.0, Spent: $835.29, Categories: 9
[PASS] 4. Added new expense: 'Organic Chemistry Lab Kit' for $42.5 (ID: 36)
[PASS] 5. Search expenses filter: found 1 item(s) matching 'Chemistry'
[PASS] 6. Affordability check: 'Gaming Monitor' -> Verdict: 🤔 Moderate Spend (11.2 hrs part-time work)
[PASS] 7. Export CSV generation successful (18 lines)
[PASS] 8. Cleaned up test expense

=======================================================
 ALL 8 INTEGRATION & END-TO-END TESTS PASSED!
=======================================================
```

---

## 🔌 API Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Register a new student account |
| `POST` | `/api/auth/login` | Authenticate and obtain session token |
| `POST` | `/api/auth/demo-login` | 1-Click login for instant demo access |
| `POST` | `/api/auth/logout` | Terminate session |
| `GET` | `/api/auth/me` | Fetch active user profile |
| `PUT` | `/api/auth/profile` | Update budget, hourly wage, university, or currency |
| `POST` | `/api/auth/reset-demo` | Restore demo data to pristine default state |
| `GET` | `/api/summary?month=YYYY-MM` | Fetch comprehensive dashboard metrics & charts data |
| `GET` | `/api/expenses?month=YYYY-MM` | List and search expenses with category filters |
| `POST` | `/api/expenses` | Record a new expense |
| `PUT` | `/api/expenses/{id}` | Update an existing expense |
| `DELETE` | `/api/expenses/{id}` | Delete an expense |
| `GET` | `/api/categories` | List user categories with spend vs limit |
| `POST` | `/api/categories` | Create custom category |
| `PUT` | `/api/categories/{id}` | Update category limit, color, or icon |
| `DELETE` | `/api/categories/{id}` | Delete custom category |
| `POST` | `/api/calculator/affordability` | Compute part-time hours and allowance impact |
| `GET` | `/api/export/csv?month=YYYY-MM` | Stream downloadable CSV report |

---

## 🔮 Future Improvements

- [ ] **Receipt Scanner (OCR)**: Take a photo of campus bookstore or cafeteria receipts to auto-extract items and prices.
- [ ] **Roommate Bill Splitting**: Shared household/apartment expense splitting with Venmo / Splitwise integration.
- [ ] **Recurring Subscription Manager**: Automated tracking and renewal alerts for student subscriptions (Spotify, Prime, Chegg).
- [ ] **Progressive Web App (PWA)**: Offline service workers and "Add to Home Screen" support on iOS & Android.
- [ ] **Real-time Foreign Exchange Rates**: Live currency conversions for international exchange students.

---

## 📄 License

This project is open-source and licensed under the [MIT License](LICENSE).

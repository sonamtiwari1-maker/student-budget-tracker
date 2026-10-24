import sqlite3
import os
import hashlib
import secrets
import calendar
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "student_budget.db")

DEFAULT_CATEGORIES = [
    {"name": "Rent & Dorm Housing", "icon": "🏠", "color": "#6366F1", "budget_limit": 450.0},
    {"name": "Groceries & Cooking", "icon": "🍎", "color": "#10B981", "budget_limit": 220.0},
    {"name": "Textbooks & Supplies", "icon": "📚", "color": "#F59E0B", "budget_limit": 100.0},
    {"name": "Campus Cafe & Dining", "icon": "☕", "color": "#EC4899", "budget_limit": 120.0},
    {"name": "Transit & Rideshare", "icon": "🚌", "color": "#06B6D4", "budget_limit": 60.0},
    {"name": "Tech & Subscriptions", "icon": "💻", "color": "#8B5CF6", "budget_limit": 45.0},
    {"name": "Entertainment & Fun", "icon": "🎮", "color": "#F97316", "budget_limit": 80.0},
    {"name": "Health & Self-Care", "icon": "🏋️", "color": "#14B8A6", "budget_limit": 45.0},
    {"name": "Emergency & Misc", "icon": "🦺", "color": "#64748B", "budget_limit": 50.0},
]

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def hash_password(password: str, salt: str = None) -> str:
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}:{hashed}"

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, hashed = stored_hash.split(":", 1)
        expected = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        return secrets.compare_digest(hashed, expected)
    except Exception:
        return False

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        university TEXT DEFAULT 'Metropolis University',
        major TEXT DEFAULT 'Computer Science',
        monthly_budget REAL DEFAULT 1200.0,
        currency TEXT DEFAULT '$',
        hourly_wage REAL DEFAULT 15.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_tokens (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        icon TEXT DEFAULT '🏷️',
        color TEXT DEFAULT '#4F46E5',
        budget_limit REAL DEFAULT 100.0,
        is_default INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        title TEXT NOT NULL,
        date TEXT NOT NULL,
        payment_method TEXT DEFAULT 'Debit Card',
        notes TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()

    seed_demo_user()

def create_user_categories(cursor, user_id):
    for cat in DEFAULT_CATEGORIES:
        cursor.execute("""
        INSERT INTO categories (user_id, name, icon, color, budget_limit, is_default)
        VALUES (?, ?, ?, ?, ?, 1)
        """, (user_id, cat["name"], cat["icon"], cat["color"], cat["budget_limit"]))

def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_tokens (token, user_id) VALUES (?, ?)", (token, user_id))
    conn.commit()
    conn.close()
    return token

def get_user_by_token(token: str):
    if not token:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.name, u.email, u.university, u.major, u.monthly_budget, u.currency, u.hourly_wage, u.created_at
        FROM users u
        JOIN user_tokens t ON u.id = t.user_id
        WHERE t.token = ?
    """, (token,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def delete_session(token: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_tokens WHERE token = ?", (token,))
    conn.commit()
    conn.close()

def seed_demo_user(force_reset: bool = False):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = 'alex@student.edu'")
    existing = cursor.fetchone()

    if existing and not force_reset:
        conn.close()
        return existing["id"]

    if existing and force_reset:
        user_id = existing["id"]
        cursor.execute("DELETE FROM expenses WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM categories WHERE user_id = ?", (user_id,))
        cursor.execute("""
            UPDATE users SET
                name = 'Alex Rivers',
                university = 'Metropolis University',
                major = 'Computer Science (Sophomore)',
                monthly_budget = 1200.0,
                currency = '$',
                hourly_wage = 16.0
            WHERE id = ?
        """, (user_id,))
    else:
        pwd_hash = hash_password("student123")
        cursor.execute("""
        INSERT INTO users (name, email, password_hash, university, major, monthly_budget, currency, hourly_wage)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("Alex Rivers", "alex@student.edu", pwd_hash, "Metropolis University", "Computer Science (Sophomore)", 1200.0, "$", 16.0))
        user_id = cursor.lastrowid

    create_user_categories(cursor, user_id)

    cursor.execute("SELECT id, name FROM categories WHERE user_id = ?", (user_id,))
    cats = {row["name"]: row["id"] for row in cursor.fetchall()}

    now = datetime.now()
    year = now.year
    month = now.month

    demo_expenses = [
        {"cat": "Rent & Dorm Housing", "amount": 450.0, "title": "Campus Housing Share (Oct)", "day": 1, "pm": "Bank Transfer", "notes": "Shared 2-bed suite"},
        {"cat": "Textbooks & Supplies", "amount": 68.50, "title": "Data Structures & Algorithms Book", "day": 2, "pm": "Debit Card", "notes": "Used copy from campus bookstore"},
        {"cat": "Groceries & Cooking", "amount": 54.20, "title": "Trader Joe's Weekly Haul", "day": 3, "pm": "Debit Card", "notes": "Eggs, oats, veggies, ramen packs"},
        {"cat": "Transit & Rideshare", "amount": 35.00, "title": "Monthly Student Transit Pass", "day": 4, "pm": "Campus Card", "notes": "50% off student discount transit"},
        {"cat": "Campus Cafe & Dining", "amount": 6.75, "title": "Library Cold Brew & Bagel", "day": 5, "pm": "Campus Card", "notes": "Study session prep"},
        {"cat": "Tech & Subscriptions", "amount": 5.99, "title": "Spotify + Hulu Student Bundle", "day": 6, "pm": "Debit Card", "notes": "Monthly subscription"},
        {"cat": "Entertainment & Fun", "amount": 14.50, "title": "Friday Movie Night with Campus Club", "day": 8, "pm": "Credit Card", "notes": "Student discount ticket"},
        {"cat": "Groceries & Cooking", "amount": 42.80, "title": "Aldi Grocery Restock", "day": 10, "pm": "Debit Card", "notes": "Protein powder, pasta, sauces"},
        {"cat": "Campus Cafe & Dining", "amount": 11.25, "title": "Campus Food Truck Burrito Bowl", "day": 12, "pm": "Cash", "notes": "Quick lunch between lectures"},
        {"cat": "Textbooks & Supplies", "amount": 18.00, "title": "Lab Notebook & Graphing Pen Set", "day": 14, "pm": "Debit Card", "notes": "For Physics 2 lab"},
        {"cat": "Health & Self-Care", "amount": 22.00, "title": "Pharmacy & Multivitamins", "day": 16, "pm": "Debit Card", "notes": "Allergy medicine & vitamin C"},
        {"cat": "Entertainment & Fun", "amount": 25.00, "title": "Board Game Cafe Social", "day": 18, "pm": "Digital Wallet", "notes": "Weekend social event"},
        {"cat": "Tech & Subscriptions", "amount": 12.00, "title": "GitHub Copilot Student / Cloud Hosting", "day": 19, "pm": "Credit Card", "notes": "Coding project hosting"},
        {"cat": "Campus Cafe & Dining", "amount": 8.50, "title": "Matcha Latte & Muffin at Cafe", "day": 20, "pm": "Campus Card", "notes": "Midterm study crunch"},
        {"cat": "Groceries & Cooking", "amount": 48.30, "title": "Local Market Produce & Snacks", "day": 22, "pm": "Debit Card", "notes": "Apples, peanut butter, bread"},
        {"cat": "Transit & Rideshare", "amount": 12.50, "title": "Late Night Rideshare from Lab", "day": 23, "pm": "Digital Wallet", "notes": "Raining after midnight lab session"},
    ]

    for exp in demo_expenses:
        cat_id = cats.get(exp["cat"])
        if cat_id:
            day = min(exp["day"], 28)
            date_str = f"{year:04d}-{month:02d}-{day:02d}"
            cursor.execute("""
            INSERT INTO expenses (user_id, category_id, amount, title, date, payment_method, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, cat_id, exp["amount"], exp["title"], date_str, exp["pm"], exp["notes"]))

    conn.commit()
    conn.close()
    return user_id

def get_dashboard_summary(user_id: int, year_month: str = None):
    now = datetime.now()
    if not year_month:
        year_month = now.strftime("%Y-%m")
    
    parts = year_month.split("-")
    year = int(parts[0])
    month = int(parts[1])
    
    _, total_days = calendar.monthrange(year, month)
    
    # Calculate days left in month
    if year == now.year and month == now.month:
        day_of_month = now.day
        days_left = max(1, total_days - day_of_month + 1)
    elif datetime(year, month, 1) < datetime(now.year, now.month, 1):
        day_of_month = total_days
        days_left = 1
    else:
        day_of_month = 1
        days_left = total_days

    conn = get_connection()
    cursor = conn.cursor()

    # User profile
    cursor.execute("SELECT monthly_budget, currency, hourly_wage FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    monthly_budget = float(user["monthly_budget"]) if user else 1000.0
    currency = user["currency"] if user else "$"
    hourly_wage = float(user["hourly_wage"]) if user and user["hourly_wage"] else 15.0

    # Total spent in the month
    start_date = f"{year_month}-01"
    end_date = f"{year_month}-{total_days:02d}"

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0.0) as total_spent, COUNT(*) as count
        FROM expenses
        WHERE user_id = ? AND date BETWEEN ? AND ?
    """, (user_id, start_date, end_date))
    spent_row = cursor.fetchone()
    total_spent = round(float(spent_row["total_spent"]), 2)
    expense_count = spent_row["count"]

    remaining_budget = round(monthly_budget - total_spent, 2)
    percent_used = round((total_spent / monthly_budget * 100.0), 1) if monthly_budget > 0 else 0.0
    
    safe_daily_spend = round(max(0.0, remaining_budget) / days_left, 2) if days_left > 0 else 0.0
    avg_daily_spent = round(total_spent / max(1, day_of_month), 2)

    # Pacing assessment
    expected_percent = round((day_of_month / total_days) * 100.0, 1)
    if remaining_budget < 0:
        pacing_status = "exceeded"
        health_label = "Budget Exceeded!"
        health_color = "#EF4444"
        health_score = 25
    elif percent_used > expected_percent + 15:
        pacing_status = "danger"
        health_label = "Over-Pacing Warning"
        health_color = "#F97316"
        health_score = 55
    elif percent_used > expected_percent + 5:
        pacing_status = "caution"
        health_label = "Caution: Spend Fast"
        health_color = "#F59E0B"
        health_score = 75
    else:
        pacing_status = "great"
        health_label = "On Track & Frugal"
        health_color = "#10B981"
        health_score = 95

    # Category breakdown
    cursor.execute("""
        SELECT c.id, c.name, c.icon, c.color, c.budget_limit,
               COALESCE(SUM(e.amount), 0.0) as spent,
               COUNT(e.id) as tx_count
        FROM categories c
        LEFT JOIN expenses e ON e.category_id = c.id AND e.date BETWEEN ? AND ?
        WHERE c.user_id = ?
        GROUP BY c.id
        ORDER BY spent DESC
    """, (start_date, end_date, user_id))
    
    categories = []
    for row in cursor.fetchall():
        spent = round(float(row["spent"]), 2)
        limit = round(float(row["budget_limit"]), 2)
        pct = round((spent / limit * 100.0), 1) if limit > 0 else 0.0
        categories.append({
            "id": row["id"],
            "name": row["name"],
            "icon": row["icon"],
            "color": row["color"],
            "budget_limit": limit,
            "spent": spent,
            "remaining": round(limit - spent, 2),
            "percent_used": pct,
            "tx_count": row["tx_count"]
        })

    # Daily trend for month
    cursor.execute("""
        SELECT date, SUM(amount) as daily_total
        FROM expenses
        WHERE user_id = ? AND date BETWEEN ? AND ?
        GROUP BY date
        ORDER BY date ASC
    """, (user_id, start_date, end_date))
    daily_rows = {r["date"]: round(float(r["daily_total"]), 2) for r in cursor.fetchall()}
    
    daily_trend = []
    for d in range(1, total_days + 1):
        d_str = f"{year_month}-{d:02d}"
        daily_trend.append({
            "day": d,
            "date": d_str,
            "amount": daily_rows.get(d_str, 0.0)
        })

    # Payment method breakdown
    cursor.execute("""
        SELECT payment_method, SUM(amount) as total, COUNT(*) as count
        FROM expenses
        WHERE user_id = ? AND date BETWEEN ? AND ?
        GROUP BY payment_method
        ORDER BY total DESC
    """, (user_id, start_date, end_date))
    payment_methods = [
        {"method": r["payment_method"], "amount": round(float(r["total"]), 2), "count": r["count"]}
        for r in cursor.fetchall()
    ]

    # Recent 6 transactions
    cursor.execute("""
        SELECT e.id, e.amount, e.title, e.date, e.payment_method, e.notes,
               c.name as category_name, c.icon as category_icon, c.color as category_color
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = ?
        ORDER BY e.date DESC, e.id DESC
        LIMIT 6
    """, (user_id,))
    recent_expenses = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return {
        "year_month": year_month,
        "monthly_budget": monthly_budget,
        "total_spent": total_spent,
        "remaining_budget": remaining_budget,
        "percent_used": percent_used,
        "expense_count": expense_count,
        "currency": currency,
        "hourly_wage": hourly_wage,
        "day_of_month": day_of_month,
        "days_in_month": total_days,
        "days_left": days_left,
        "safe_daily_spend": safe_daily_spend,
        "avg_daily_spent": avg_daily_spent,
        "pacing_status": pacing_status,
        "health_label": health_label,
        "health_color": health_color,
        "health_score": health_score,
        "categories": categories,
        "daily_trend": daily_trend,
        "payment_methods": payment_methods,
        "recent_expenses": recent_expenses
    }

import os
import io
import csv
from datetime import datetime
from contextlib import asynccontextmanager
from starlette.applications import Starlette
from starlette.responses import JSONResponse, FileResponse, Response
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

import database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Ensure database is initialized
database.init_db()

@asynccontextmanager
async def lifespan(app):
    database.init_db()
    yield

# Helper to authenticate requests
def get_authenticated_user(request):
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    elif "sbt_token" in request.query_params:
        token = request.query_params["sbt_token"]

    if not token:
        return None
    return database.get_user_by_token(token)

def unauthorized():
    return JSONResponse({"error": "Please log in to continue"}, status_code=401)

# Routes
async def serve_index(request):
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

# Auth endpoints
async def api_register(request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()
    university = data.get("university", "State University").strip()
    major = data.get("major", "General Studies").strip()
    monthly_budget = float(data.get("monthly_budget", 1000.0))
    currency = data.get("currency", "$").strip()
    hourly_wage = float(data.get("hourly_wage", 15.0))

    if not name or not email or not password:
        return JSONResponse({"error": "Name, email, and password are required."}, status_code=400)

    if len(password) < 6:
        return JSONResponse({"error": "Password must be at least 6 characters."}, status_code=400)

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return JSONResponse({"error": "An account with this email already exists."}, status_code=409)

    pwd_hash = database.hash_password(password)
    cursor.execute("""
        INSERT INTO users (name, email, password_hash, university, major, monthly_budget, currency, hourly_wage)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, email, pwd_hash, university, major, monthly_budget, currency, hourly_wage))
    user_id = cursor.lastrowid
    database.create_user_categories(cursor, user_id)
    conn.commit()
    conn.close()

    token = database.create_session(user_id)
    user = database.get_user_by_token(token)
    return JSONResponse({"message": "Registration successful", "token": token, "user": user})

async def api_login(request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    if not email or not password:
        return JSONResponse({"error": "Email and password are required."}, status_code=400)

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,))
    user_row = cursor.fetchone()
    conn.close()

    if not user_row or not database.verify_password(password, user_row["password_hash"]):
        return JSONResponse({"error": "Invalid email or password."}, status_code=401)

    token = database.create_session(user_row["id"])
    user = database.get_user_by_token(token)
    return JSONResponse({"message": "Login successful", "token": token, "user": user})

async def api_demo_login(request):
    user_id = database.seed_demo_user()
    token = database.create_session(user_id)
    user = database.get_user_by_token(token)
    return JSONResponse({"message": "Logged in as Demo Student", "token": token, "user": user})

async def api_logout(request):
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        database.delete_session(token)
    return JSONResponse({"message": "Logged out successfully"})

async def api_me(request):
    user = get_authenticated_user(request)
    if not user:
        return unauthorized()
    return JSONResponse({"user": user})

async def api_update_profile(request):
    user = get_authenticated_user(request)
    if not user:
        return unauthorized()

    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    name = data.get("name", user["name"]).strip()
    university = data.get("university", user["university"]).strip()
    major = data.get("major", user["major"]).strip()
    monthly_budget = float(data.get("monthly_budget", user["monthly_budget"]))
    currency = data.get("currency", user["currency"]).strip()
    hourly_wage = float(data.get("hourly_wage", user["hourly_wage"]))

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET name = ?, university = ?, major = ?, monthly_budget = ?, currency = ?, hourly_wage = ?
        WHERE id = ?
    """, (name, university, major, monthly_budget, currency, hourly_wage, user["id"]))
    conn.commit()
    conn.close()

    auth_header = request.headers.get("Authorization", "")
    token = auth_header.split(" ", 1)[1].strip()
    updated = database.get_user_by_token(token)
    return JSONResponse({"message": "Profile updated", "user": updated})

async def api_reset_demo(request):
    user = get_authenticated_user(request)
    if not user:
        return unauthorized()
    database.seed_demo_user(force_reset=True)
    return JSONResponse({"message": "Demo data has been refreshed!"})

# Dashboard Summary
async def api_get_summary(request):
    user = get_authenticated_user(request)
    if not user:
        return unauthorized()

    month = request.query_params.get("month")
    summary = database.get_dashboard_summary(user["id"], month)
    return JSONResponse(summary)

# Expenses endpoints
async def api_get_expenses(request):
    user = get_authenticated_user(request)
    if not user:
        return unauthorized()

    month = request.query_params.get("month")
    category_id = request.query_params.get("category_id")
    search = request.query_params.get("search", "").strip()

    conn = database.get_connection()
    cursor = conn.cursor()

    query = """
        SELECT e.id, e.amount, e.title, e.date, e.payment_method, e.notes, e.created_at,
               c.id as category_id, c.name as category_name, c.icon as category_icon, c.color as category_color
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = ?
    """
    params = [user["id"]]

    if month:
        query += " AND e.date LIKE ?"
        params.append(f"{month}%")

    if category_id and category_id.isdigit():
        query += " AND e.category_id = ?"
        params.append(int(category_id))

    if search:
        query += " AND (e.title LIKE ? OR e.notes LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term])

    query += " ORDER BY e.date DESC, e.id DESC"

    cursor.execute(query, params)
    expenses = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return JSONResponse({"expenses": expenses})

async def api_create_expense(request):
    user = get_authenticated_user(request)
    if not user:
        return unauthorized()

    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    title = data.get("title", "").strip()
    amount = float(data.get("amount", 0.0))
    category_id = int(data.get("category_id", 0))
    date_str = data.get("date", datetime.now().strftime("%Y-%m-%d")).strip()
    payment_method = data.get("payment_method", "Debit Card").strip()
    notes = data.get("notes", "").strip()

    if not title or amount <= 0 or not category_id:
        return JSONResponse({"error": "Title, valid positive amount, and category are required."}, status_code=400)

    conn = database.get_connection()
    cursor = conn.cursor()

    # Verify category belongs to user
    cursor.execute("SELECT id FROM categories WHERE id = ? AND user_id = ?", (category_id, user["id"]))
    if not cursor.fetchone():
        conn.close()
        return JSONResponse({"error": "Invalid category for user."}, status_code=400)

    cursor.execute("""
        INSERT INTO expenses (user_id, category_id, amount, title, date, payment_method, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user["id"], category_id, amount, title, date_str, payment_method, notes))
    exp_id = cursor.lastrowid
    conn.commit()

    cursor.execute("""
        SELECT e.id, e.amount, e.title, e.date, e.payment_method, e.notes,
               c.id as category_id, c.name as category_name, c.icon as category_icon, c.color as category_color
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.id = ?
    """, (exp_id,))
    expense = dict(cursor.fetchone())
    conn.close()

    return JSONResponse({"message": "Expense added successfully", "expense": expense}, status_code=201)

async def api_update_expense(request):
    user = get_authenticated_user(request)
    if not user:
        return unauthorized()

    expense_id = request.path_params["id"]
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    title = data.get("title", "").strip()
    amount = float(data.get("amount", 0.0))
    category_id = int(data.get("category_id", 0))
    date_str = data.get("date", "").strip()
    payment_method = data.get("payment_method", "Debit Card").strip()
    notes = data.get("notes", "").strip()

    if not title or amount <= 0 or not category_id:
        return JSONResponse({"error": "Title, positive amount, and category are required."}, status_code=400)

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE expenses
        SET title = ?, amount = ?, category_id = ?, date = ?, payment_method = ?, notes = ?
        WHERE id = ? AND user_id = ?
    """, (title, amount, category_id, date_str, payment_method, notes, expense_id, user["id"]))
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()

    if not updated:
        return JSONResponse({"error": "Expense not found or unauthorized"}, status_code=404)

    return JSONResponse({"message": "Expense updated successfully"})

async def api_delete_expense(request):
    user = get_authenticated_user(request)
    if not user:
        return unauthorized()

    expense_id = request.path_params["id"]
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user["id"]))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()

    if not deleted:
        return JSONResponse({"error": "Expense not found or unauthorized"}, status_code=404)

    return JSONResponse({"message": "Expense deleted successfully"})

# Categories endpoints
async def api_get_categories(request):
    user = get_authenticated_user(request)
    if not user:
        return unauthorized()

    month = request.query_params.get("month", datetime.now().strftime("%Y-%m"))
    start_date = f"{month}-01"
    end_date = f"{month}-31"

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.name, c.icon, c.color, c.budget_limit, c.is_default,
               COALESCE(SUM(e.amount), 0.0) as spent
        FROM categories c
        LEFT JOIN expenses e ON e.category_id = c.id AND e.date BETWEEN ? AND ?
        WHERE c.user_id = ?
        GROUP BY c.id
        ORDER BY c.id ASC
    """, (start_date, end_date, user["id"]))
    categories = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return JSONResponse({"categories": categories})

async def api_create_category(request):
    user = get_authenticated_user(request)
    if not user:
        return unauthorized()

    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    name = data.get("name", "").strip()
    icon = data.get("icon", "🏷️").strip()
    color = data.get("color", "#4F46E5").strip()
    budget_limit = float(data.get("budget_limit", 100.0))

    if not name or budget_limit <= 0:
        return JSONResponse({"error": "Category name and a positive budget limit are required."}, status_code=400)

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO categories (user_id, name, icon, color, budget_limit, is_default)
        VALUES (?, ?, ?, ?, ?, 0)
    """, (user["id"], name, icon, color, budget_limit))
    cat_id = cursor.lastrowid
    conn.commit()

    cursor.execute("SELECT * FROM categories WHERE id = ?", (cat_id,))
    new_cat = dict(cursor.fetchone())
    conn.close()

    return JSONResponse({"message": "Category created", "category": new_cat}, status_code=201)

async def api_update_category(request):
    user = get_authenticated_user(request)
    if not user:
        return unauthorized()

    category_id = request.path_params["id"]
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    name = data.get("name", "").strip()
    icon = data.get("icon", "🏷️").strip()
    color = data.get("color", "#4F46E5").strip()
    budget_limit = float(data.get("budget_limit", 100.0))

    if not name or budget_limit <= 0:
        return JSONResponse({"error": "Name and positive budget limit are required."}, status_code=400)

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE categories
        SET name = ?, icon = ?, color = ?, budget_limit = ?
        WHERE id = ? AND user_id = ?
    """, (name, icon, color, budget_limit, category_id, user["id"]))
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()

    if not updated:
        return JSONResponse({"error": "Category not found"}, status_code=404)

    return JSONResponse({"message": "Category updated successfully"})

async def api_delete_category(request):
    user = get_authenticated_user(request)
    if not user:
        return unauthorized()

    category_id = request.path_params["id"]
    conn = database.get_connection()
    cursor = conn.cursor()
    
    # Check if category has expenses
    cursor.execute("SELECT COUNT(*) as c FROM expenses WHERE category_id = ? AND user_id = ?", (category_id, user["id"]))
    row = cursor.fetchone()
    if row and row["c"] > 0:
        conn.close()
        return JSONResponse({"error": f"Cannot delete category: it still has {row['c']} expense(s) linked to it. Reassign or delete those expenses first."}, status_code=400)

    cursor.execute("DELETE FROM categories WHERE id = ? AND user_id = ?", (category_id, user["id"]))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()

    if not deleted:
        return JSONResponse({"error": "Category not found"}, status_code=404)

    return JSONResponse({"message": "Category deleted successfully"})

# Student "Can I Afford It?" Reality Check Calculator
async def api_affordability_check(request):
    user = get_authenticated_user(request)
    if not user:
        return unauthorized()

    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    item_name = data.get("item_name", "Desired Item").strip()
    price = float(data.get("price", 0.0))

    if price <= 0:
        return JSONResponse({"error": "Please enter a valid price."}, status_code=400)

    summary = database.get_dashboard_summary(user["id"])
    remaining_budget = summary["remaining_budget"]
    safe_daily_spend = summary["safe_daily_spend"]
    hourly_wage = summary["hourly_wage"]
    currency = summary["currency"]

    hours_of_work = round(price / max(1.0, hourly_wage), 1)
    percent_of_monthly = round((price / max(1.0, summary["monthly_budget"])) * 100.0, 1)
    days_of_allowance = round(price / max(1.0, safe_daily_spend), 1) if safe_daily_spend > 0 else 999.0
    balance_after = round(remaining_budget - price, 2)

    if balance_after < 0:
        verdict = "🚨 Budget Breaker"
        verdict_class = "danger"
        advice = f"Buying this puts you {currency}{abs(balance_after):.2f} into the red! Delay this purchase until next month or look for student discounts."
    elif days_of_allowance > 7:
        verdict = "⚠️ High Impact Purchase"
        verdict_class = "caution"
        advice = f"This cost equals {days_of_allowance} full days of your daily allowance ({hours_of_work} work hours). Sleep on it for 48 hours to avoid impulse buying!"
    elif days_of_allowance > 3:
        verdict = "🤔 Moderate Spend"
        verdict_class = "moderate"
        advice = f"Doable, but it consumes ~{days_of_allowance} days of your spending allowance. Make sure essentials like rent and food are covered first."
    else:
        verdict = "✅ Student Approved"
        verdict_class = "safe"
        advice = f"Nicely within your daily buffer! It only takes {hours_of_work} hours of work at your {currency}{hourly_wage:.2f}/hr rate."

    return JSONResponse({
        "item_name": item_name,
        "price": price,
        "hours_of_work": hours_of_work,
        "percent_of_monthly": percent_of_monthly,
        "days_of_allowance": days_of_allowance,
        "balance_after": balance_after,
        "verdict": verdict,
        "verdict_class": verdict_class,
        "advice": advice
    })

# Export Expenses to CSV
async def api_export_csv(request):
    user = get_authenticated_user(request)
    if not user:
        return unauthorized()

    month = request.query_params.get("month")
    conn = database.get_connection()
    cursor = conn.cursor()

    query = """
        SELECT e.date, e.title, e.amount, c.name as category, e.payment_method, e.notes
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = ?
    """
    params = [user["id"]]
    if month:
        query += " AND e.date LIKE ?"
        params.append(f"{month}%")
    query += " ORDER BY e.date ASC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Description", "Amount", "Category", "Payment Method", "Notes"])
    for r in rows:
        writer.writerow([r["date"], r["title"], f"{r['amount']:.2f}", r["category"], r["payment_method"], r["notes"]])

    filename = f"student_expenses_{month if month else 'all'}.csv"
    headers = {
        "Content-Disposition": f"attachment; filename=\"{filename}\"",
        "Content-Type": "text/csv; charset=utf-8"
    }
    return Response(output.getvalue(), headers=headers, media_type="text/csv")


# Route table
routes = [
    Route("/", endpoint=serve_index),
    # Auth
    Route("/api/auth/register", endpoint=api_register, methods=["POST"]),
    Route("/api/auth/login", endpoint=api_login, methods=["POST"]),
    Route("/api/auth/demo-login", endpoint=api_demo_login, methods=["POST"]),
    Route("/api/auth/logout", endpoint=api_logout, methods=["POST"]),
    Route("/api/auth/me", endpoint=api_me, methods=["GET"]),
    Route("/api/auth/profile", endpoint=api_update_profile, methods=["PUT"]),
    Route("/api/auth/reset-demo", endpoint=api_reset_demo, methods=["POST"]),
    # Dashboard summary
    Route("/api/summary", endpoint=api_get_summary, methods=["GET"]),
    # Expenses
    Route("/api/expenses", endpoint=api_get_expenses, methods=["GET"]),
    Route("/api/expenses", endpoint=api_create_expense, methods=["POST"]),
    Route("/api/expenses/{id:int}", endpoint=api_update_expense, methods=["PUT"]),
    Route("/api/expenses/{id:int}", endpoint=api_delete_expense, methods=["DELETE"]),
    # Categories
    Route("/api/categories", endpoint=api_get_categories, methods=["GET"]),
    Route("/api/categories", endpoint=api_create_category, methods=["POST"]),
    Route("/api/categories/{id:int}", endpoint=api_update_category, methods=["PUT"]),
    Route("/api/categories/{id:int}", endpoint=api_delete_category, methods=["DELETE"]),
    # Student Calculator & Tools
    Route("/api/calculator/affordability", endpoint=api_affordability_check, methods=["POST"]),
    Route("/api/export/csv", endpoint=api_export_csv, methods=["GET"]),
    # Static files mount
    Mount("/static", app=StaticFiles(directory=STATIC_DIR), name="static"),
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = Starlette(debug=True, routes=routes, middleware=middleware, lifespan=lifespan)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

from starlette.testclient import TestClient
from app import app
import json

def run_tests():
    client = TestClient(app)

    # 1. Test index page
    res = client.get('/')
    assert res.status_code == 200, f"Index failed: {res.status_code}"
    assert "UniBudget" in res.text
    print("[PASS] 1. Index page served successfully (200 OK)")

    # 2. Test demo login
    res = client.post('/api/auth/demo-login')
    assert res.status_code == 200, f"Demo login failed: {res.status_code}"
    data = res.json()
    assert "token" in data
    token = data["token"]
    user = data["user"]
    print(f"[PASS] 2. Demo student login: {user['name']} ({user['university']})")

    # 3. Test dashboard summary
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get('/api/summary', headers=headers)
    assert res.status_code == 200, f"Summary failed: {res.status_code}"
    summary = res.json()
    assert "monthly_budget" in summary
    assert len(summary["categories"]) > 0
    print(f"[PASS] 3. Dashboard summary: Budget {summary['currency']}{summary['monthly_budget']}, Spent: {summary['currency']}{summary['total_spent']}, Categories: {len(summary['categories'])}")

    # 4. Test adding an expense
    new_exp = {
        "title": "Organic Chemistry Lab Kit",
        "amount": 42.50,
        "category_id": summary["categories"][0]["id"],
        "date": "2026-10-15",
        "payment_method": "Campus Card",
        "notes": "Chem 102 required kit"
    }
    res = client.post('/api/expenses', json=new_exp, headers=headers)
    assert res.status_code == 201, f"Create expense failed: {res.status_code}"
    exp_data = res.json()
    created_id = exp_data["expense"]["id"]
    print(f"[PASS] 4. Added new expense: '{new_exp['title']}' for {summary['currency']}{new_exp['amount']} (ID: {created_id})")

    # 5. Test expenses listing & search filter
    res = client.get(f'/api/expenses?search=Chemistry', headers=headers)
    assert res.status_code == 200
    search_results = res.json()["expenses"]
    assert len(search_results) >= 1
    print(f"[PASS] 5. Search expenses filter: found {len(search_results)} item(s) matching 'Chemistry'")

    # 6. Test affordability calculator
    res = client.post('/api/calculator/affordability', json={"item_name": "Gaming Monitor", "price": 180.0}, headers=headers)
    assert res.status_code == 200
    calc = res.json()
    print(f"[PASS] 6. Affordability check: '{calc['item_name']}' -> Verdict: {calc['verdict']} ({calc['hours_of_work']} hrs part-time work)")

    # 7. Test CSV Export
    res = client.get('/api/export/csv', headers=headers)
    assert res.status_code == 200
    assert "text/csv" in res.headers.get("content-type", "")
    assert "Chemistry" in res.text
    print(f"[PASS] 7. Export CSV generation successful ({len(res.text.splitlines())} lines)")

    # 8. Clean up created test expense
    del_res = client.delete(f'/api/expenses/{created_id}', headers=headers)
    assert del_res.status_code == 200
    print(f"[PASS] 8. Cleaned up test expense")

    print("\n=======================================================")
    print(" ALL 8 INTEGRATION & END-TO-END TESTS PASSED!")
    print("=======================================================\n")

if __name__ == "__main__":
    run_tests()

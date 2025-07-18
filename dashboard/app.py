from flask import Flask, jsonify, request
from flask_cors import CORS
from collections import defaultdict
from datetime import datetime
import calendar

app = Flask(__name__)
CORS(app)

data = [
  { 'user_id': 'jojo', 'date': '2025-06-01', 'category': 'Fast Food', 'total': 12.45 },
  { 'user_id': 'jojo', 'date': '2025-06-01', 'category': 'Groceries', 'total': 28.90 },
  { 'user_id': 'jojo', 'date': '2025-06-02', 'category': 'Transportation', 'total': 15.00 },
  { 'user_id': 'jojo', 'date': '2025-06-02', 'category': 'Fast Food', 'total': 8.75 },
  { 'user_id': 'jojo', 'date': '2025-06-03', 'category': 'Groceries', 'total': 35.60 },
  { 'user_id': 'jojo', 'date': '2025-06-04', 'category': 'Entertainment', 'total': 20.00 },
  { 'user_id': 'jojo', 'date': '2025-06-05', 'category': 'Fast Food', 'total': 43.8 },
  { 'user_id': 'jojo', 'date': '2025-06-05', 'category': 'Groceries', 'total': 7.75 },
  { 'user_id': 'jojo', 'date': '2025-06-05', 'category': 'Fast Food', 'total': 43.85 },
  { 'user_id': 'jojo', 'date': '2025-06-05', 'category': 'Groceries', 'total': 9.95 },
  { 'user_id': 'jojo', 'date': '2025-06-06', 'category': 'Bills', 'total': 120.00 },
  { 'user_id': 'jojo', 'date': '2025-06-07', 'category': 'Fast Food', 'total': 14.25 },
  { 'user_id': 'jojo', 'date': '2025-06-08', 'category': 'Transportation', 'total': 10.00 },
  { 'user_id': 'alex', 'date': '2025-06-01', 'category': 'Groceries', 'total': 23.45 },
  { 'user_id': 'alex', 'date': '2025-06-02', 'category': 'Utilities', 'total': 45.00 },
  { 'user_id': 'alex', 'date': '2025-06-02', 'category': 'Fast Food', 'total': 13.99 },
  { 'user_id': 'alex', 'date': '2025-06-03', 'category': 'Entertainment', 'total': 60.00 },
  { 'user_id': 'alex', 'date': '2025-06-04', 'category': 'Groceries', 'total': 18.30 },
  { 'user_id': 'alex', 'date': '2025-06-05', 'category': 'Transportation', 'total': 9.50 },
  { 'user_id': 'alex', 'date': '2025-06-06', 'category': 'Fast Food', 'total': 7.85 },
  { 'user_id': 'alex', 'date': '2025-06-07', 'category': 'Groceries', 'total': 34.20 },
  { 'user_id': 'sam', 'date': '2025-06-01', 'category': 'Groceries', 'total': 50.00 },
  { 'user_id': 'sam', 'date': '2025-06-02', 'category': 'Entertainment', 'total': 45.00 },
  { 'user_id': 'sam', 'date': '2025-06-03', 'category': 'Fast Food', 'total': 25.00 },
  { 'user_id': 'sam', 'date': '2025-06-04', 'category': 'Transportation', 'total': 5.50 },
  { 'user_id': 'sam', 'date': '2025-06-05', 'category': 'Groceries', 'total': 60.75 },
  { 'user_id': 'sam', 'date': '2025-06-06', 'category': 'Bills', 'total': 200.00 },
  { 'user_id': 'sam', 'date': '2025-06-07', 'category': 'Fast Food', 'total': 11.95 },
  { 'user_id': 'sam', 'date': '2025-06-08', 'category': 'Entertainment', 'total': 30.00 },
  { 'user_id': 'sam', 'date': '2025-06-09', 'category': 'Groceries', 'total': 42.10 },
  { 'user_id': 'jojo', 'date': '2025-06-09', 'category': 'Medical', 'total': 75.00 },
  { 'user_id': 'alex', 'date': '2025-06-09', 'category': 'Groceries', 'total': 22.95 },
  { 'user_id': 'sam', 'date': '2025-06-10', 'category': 'Transportation', 'total': 6.80 }
]

@app.route("/summary")
def summary():
    user_id = request.args.get("user_id")
    user_data = [entry for entry in data if entry["user_id"] == user_id]

    if not user_data:
        return jsonify({"error": "No data found"}), 404

    total_spend = sum(entry["total"] for entry in user_data)
    unique_days = set(entry["date"] for entry in user_data)
    avg_daily_spend = total_spend / len(unique_days)

    # Top category
    category_totals = defaultdict(float)
    for entry in user_data:
        category_totals[entry["category"]] += entry["total"]

    top_category = max(category_totals.items(), key=lambda x: x[1])

    # Expense by category (for donut)
    expense_by_category = {
        "labels": list(category_totals.keys()),
        "values": list(category_totals.values())
    }

    # Weekly Spending (group by weekday)
    weekly = defaultdict(float)
    for entry in user_data:
        weekday = datetime.strptime(entry["date"], "%Y-%m-%d").weekday()  # 0 = Monday
        weekly[calendar.day_name[weekday]] += entry["total"]

    # Sort weekdays in order
    ordered_week = [calendar.day_name[i] for i in range(7)]
    weekly_spending = {
        "labels": ordered_week,
        "values": [round(weekly[day], 2) for day in ordered_week]
    }

    return jsonify({
        "total_monthly_spend": round(total_spend, 2),
        "average_daily_spend": round(avg_daily_spend, 2),
        "top_category": top_category[0],
        "top_category_total": round(top_category[1], 2),
        "expense_by_category": expense_by_category,
        "weekly_spending": weekly_spending
    })

if __name__ == "__main__":
    app.run(debug=True)

from datetime import datetime, timedelta
from flask import redirect, render_template, session
from functools import wraps
import hashlib  # Import hashlib for creating alert hashes
import math
import requests

# NEW IMPORTS FOR SQLALCHEMY
from sqlalchemy import text, func


# Helper function to execute a query and fetch results as dictionaries
# This function is designed to be passed the 'db' instance from app.py
def execute_query_helper(db_instance, sql_query, params=None, fetch_one=False):
    """
    Executes a raw SQL query using SQLAlchemy's session and returns results
    as a list of dictionaries (or a single dictionary if fetch_one is True).
    """
    if params is None:
        params = {}
    
    # Ensure all operations are within a transaction
    try:
        result = db_instance.session.execute(text(sql_query), params)
        if fetch_one:
            row = result.fetchone()
            return dict(row._mapping) if row else None
        else:
            return [dict(row._mapping) for row in result.fetchall()]
    except Exception as e:
        # Rollback the session in case of an error during query execution
        db_instance.session.rollback()
        raise e # Re-raise the exception after rollback to handle in Flask route


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


# Helper function to gather all raw and derived financial metrics
# Now accepts 'db_instance' as an argument
def _get_all_financial_metrics(db_instance, user_id):
    """Gathers all necessary financial metrics for alert generation and health score."""

    # --- Savings Goal Tracker ---
    savings_goals_raw = execute_query_helper(db_instance, """
        SELECT id, goal, amount, target_amount FROM savings WHERE user_id = :user_id
    """, {"user_id": user_id})

    savings_goals = []
    if savings_goals_raw:
        for item in savings_goals_raw:
            current_amount = float(item['amount']) # Ensure amount is float for calculations
            target_amount = float(item['target_amount']) if item['target_amount'] is not None else 0.0

            if target_amount <= 0:
                progress_percentage = 0
            else:
                progress_percentage = (current_amount / target_amount * 100)
                progress_percentage = min(progress_percentage, 100)

            savings_goals.append({
                "id": item['id'],
                "goal": item['goal'],
                "current_amount": current_amount,
                "target_amount": target_amount,
                "progress_percentage": round(progress_percentage, 2)
            })

    # --- Financial Data for Cash Flow ---
    all_income_items = execute_query_helper(db_instance, "SELECT amount FROM income WHERE user_id = :user_id", {"user_id": user_id})
    all_total_income = sum(float(item['amount']) for item in all_income_items) if all_income_items else 0.0

    all_expenses_items = execute_query_helper(db_instance, "SELECT amount FROM expenses WHERE user_id = :user_id", {"user_id": user_id})
    all_total_expenses = sum(float(item['amount']) for item in all_expenses_items) if all_expenses_items else 0.0

    cash_flow = all_total_income - all_total_expenses

    # --- Net Worth Tracker (Traditional: Assets - Liabilities) ---
    # total_assets previously was sum of savings_goals.current_amount. Let's keep that for now.
    total_assets = sum(goal['current_amount'] for goal in savings_goals) if savings_goals else 0.0

    total_liabilities_result = execute_query_helper(db_instance, """
        SELECT SUM(current_balance) AS total_debt FROM debt WHERE user_id = :user_id
    """, {"user_id": user_id}, fetch_one=True)
    total_liabilities = float(total_liabilities_result['total_debt']) if total_liabilities_result and total_liabilities_result['total_debt'] is not None else 0.0

    debt_items = execute_query_helper(db_instance, "SELECT id, debt_name, current_balance, due_date FROM debt WHERE user_id = :user_id", {"user_id": user_id})
    if not debt_items:
        debt_items = []
    # Ensure current_balance in debt_items is float
    for debt in debt_items:
        debt['current_balance'] = float(debt['current_balance'])

    # --- Additional data for Budget vs Actual for alerts ---
    current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    current_month_str = current_month_start.strftime('%Y-%m') # YYYY-MM format

    budget_data_raw = execute_query_helper(db_instance, """
        SELECT category, amount FROM budget WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :current_month
    """, {"user_id": user_id, "current_month": current_month_str})

    expenses_data_raw = execute_query_helper(db_instance, """
        SELECT category, amount FROM expenses WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :current_month
    """, {"user_id": user_id, "current_month": current_month_str})

    budget_vs_actual = {}
    for item in budget_data_raw:
        category = item['category']
        if category not in budget_vs_actual:
            budget_vs_actual[category] = {'budgeted': 0.0, 'spent': 0.0, 'remaining': 0.0}
        budget_vs_actual[category]['budgeted'] += float(item['amount'])

    for item in expenses_data_raw:
        category = item['category']
        if category not in budget_vs_actual:
            budget_vs_actual[category] = {'budgeted': 0.0, 'spent': 0.0, 'remaining': 0.0}
        budget_vs_actual[category]['spent'] += float(item['amount'])

    for category in budget_vs_actual:
        budget_vs_actual[category]['remaining'] = budget_vs_actual[category]['budgeted'] - budget_vs_actual[category]['spent']

    # --- Financial Health Score Calculation ---
    num_months_expenses_result = execute_query_helper(db_instance,
        "SELECT COUNT(DISTINCT TO_CHAR(date, 'YYYY-MM')) AS num_months FROM expenses WHERE user_id = :user_id",
        {"user_id": user_id}, fetch_one=True)
    num_months_expenses = num_months_expenses_result['num_months'] if num_months_expenses_result and num_months_expenses_result['num_months'] is not None else 0

    financial_health_score = 0
    score_details = []

    if (all_total_income == 0 and all_total_expenses == 0 and
        total_assets == 0 and total_liabilities == 0 and
        not savings_goals and not debt_items):
        financial_health_score = 0
        score_details.append("No financial data recorded yet. Add some data to see your score!")
    else:
        total_current_savings = sum(goal['current_amount'] for goal in savings_goals) if savings_goals else 0.0

        # 1. Savings Rate
        savings_rate = 0.0
        savings_rate_score = 0
        if all_total_income > 0:
            savings_rate = (total_current_savings / all_total_income * 100)
            if savings_rate >= 20:
                savings_rate_score = 40
            elif savings_rate >= 10:
                savings_rate_score = 25
            else:
                savings_rate_score = 10
        else:
            savings_rate_score = 0
            savings_rate = 0.0
        financial_health_score += savings_rate_score
        score_details.append(f"Savings Rate: {round(savings_rate, 2)}% ({savings_rate_score} points)")

        # 2. Debt-to-Asset Ratio
        debt_to_asset_ratio = 0.0
        debt_score = 0
        if total_liabilities == 0 and total_assets == 0:
            debt_score = 30
        elif total_assets > 0:
            debt_to_asset_ratio = (total_liabilities / total_assets * 100)
            if debt_to_asset_ratio <= 30:
                debt_score = 30
            elif debt_to_asset_ratio <= 60:
                debt_score = 15
            else:
                debt_score = 5
        else:
            debt_score = 5
            debt_to_asset_ratio = float('inf')

        financial_health_score += debt_score
        if math.isinf(debt_to_asset_ratio):
            score_details.append(f"Debt-to-Asset Ratio: Infinite% ({debt_score} points) - Total Debt: ${total_liabilities:,.2f}")
        else:
            score_details.append(
                f"Debt-to-Asset Ratio: {round(debt_to_asset_ratio, 2)}% ({debt_score} points) - Total Debt: ${total_liabilities:,.2f}")

        # 3. Emergency Fund
        average_monthly_expenses = 0.0
        if num_months_expenses > 0:
            average_monthly_expenses = all_total_expenses / num_months_expenses

        emergency_fund_target = average_monthly_expenses * 3

        emergency_fund_score = 0
        if average_monthly_expenses > 0:
            if total_current_savings >= emergency_fund_target:
                emergency_fund_score = 30
            elif total_current_savings >= emergency_fund_target * 0.5:
                emergency_fund_score = 15
            else:
                emergency_fund_score = 5
        else:
            emergency_fund_score = 0
        financial_health_score += emergency_fund_score
        score_details.append(
            f"Emergency Fund Coverage (vs 3 months avg expenses ${average_monthly_expenses:,.2f}): Current Savings: ${total_current_savings:,.2f} ({emergency_fund_score} points)")

        calculated_net_worth = total_assets - total_liabilities
        score_details.append(f"Net Worth: ${calculated_net_worth:,.2f}")

    financial_health_score = min(financial_health_score, 100)

    # Calculate emergency_fund_coverage in months for the AI prompt
    emergency_fund_coverage = 0.0
    if average_monthly_expenses > 0:
        emergency_fund_coverage = total_current_savings / average_monthly_expenses

    return {
        "all_total_income": all_total_income,
        "all_total_expenses": all_total_expenses,
        "cash_flow": cash_flow,
        "total_assets": total_assets,
        "total_liabilities": total_liabilities, # This is 'current_debt' for AI prompt
        "savings_goals": savings_goals,
        "debt_items": debt_items,
        "budget_vs_actual": budget_vs_actual,
        "financial_health_score": financial_health_score,
        "score_details": score_details,
        "average_monthly_expenses": average_monthly_expenses,
        "emergency_fund_target_3_months": emergency_fund_target, # New: for AI prompt
        "emergency_fund_coverage": emergency_fund_coverage, # New: for AI prompt
        "over_budget_categories": [cat for cat, data in budget_vs_actual.items() if data['remaining'] < 0],
        "top_spending_categories_str": ", ".join([cat for cat, data in sorted(budget_vs_actual.items(), key=lambda item: item[1]['spent'], reverse=True)[:5] if data['spent'] > 0])
    }


# Now accepts 'db_instance' as an argument
def _generate_financial_alerts_list(db_instance, user_id):
    """Generates a list of financial alert messages based on user data."""
    # Pass db_instance to _get_all_financial_metrics
    metrics = _get_all_financial_metrics(db_instance, user_id)
    alerts = []
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    dismissed_alerts_hashes = set()
    dismissed_alerts_db = execute_query_helper(db_instance, "SELECT alert_hash FROM read_user_alerts WHERE user_id = :user_id", {"user_id": user_id})
    if dismissed_alerts_db:
        for row in dismissed_alerts_db:
            dismissed_alerts_hashes.add(row['alert_hash'])

    generated_alerts = []

    # 1. Overbudget Alerts
    for category, data in metrics["budget_vs_actual"].items():
        message = None
        if data['remaining'] < 0:
            message = f"Heads up! You're **${abs(data['remaining']):.2f} over budget** for **{category}** this month. Time to adjust?"
            alert_type = "warning"
            icon = "fas fa-exclamation-triangle"
        elif data['budgeted'] > 0 and data['remaining'] == data['budgeted'] and data['spent'] == 0: # Only if nothing spent
            message = f"Great start! You've budgeted **${data['budgeted']:.2f}** for **{category}** and haven't spent anything yet."
            alert_type = "info"
            icon = "fas fa-check-circle"

        if message:
            alert_hash_base = f"budget_alert_{category}_{today.strftime('%Y-%m')}"
            alert_hash = hashlib.md5(alert_hash_base.encode()).hexdigest()

            if alert_hash not in dismissed_alerts_hashes:
                generated_alerts.append({
                    "type": alert_type,
                    "message": message,
                    "icon": icon,
                    "alert_hash": alert_hash,
                    "is_read": False
                })

    # 2. Debt Due Soon Alerts
    for debt in metrics["debt_items"]:
        message = None
        alert_type = None
        icon = None
        if debt['due_date']: # Ensure due_date exists
            try:
                # Assuming debt['due_date'] might come as a datetime object directly from SQLAlchemy
                # or as a string if using direct query and not converting.
                # It's safer to ensure it's a datetime object.
                if isinstance(debt['due_date'], str):
                    due_date_dt = datetime.strptime(debt['due_date'], '%Y-%m-%d')
                else: # Assume it's already a datetime object
                    due_date_dt = debt['due_date']


                time_diff = due_date_dt - today
                diff_days = time_diff.days

                if diff_days >= 0 and diff_days <= 7:
                    message = f"Action Required: Your **{debt['debt_name']}** payment of **${debt['current_balance']:.2f}** is due in **{diff_days} day(s)**! Don't miss it!"
                    alert_type = "danger"
                    icon = "fas fa-calendar-times"
                elif diff_days < 0 and abs(diff_days) < 30:
                    message = f"Urgent: Your **{debt['debt_name']}** payment was due **{abs(diff_days)} day(s) ago**. Please address this promptly!"
                    alert_type = "danger"
                    icon = "fas fa-bell"
            except (ValueError, TypeError) as e:
                print(f"Warning: Could not parse or process debt due date for debt ID {debt.get('id', 'N/A')}: {debt['due_date']} - Error: {e}")

        if message:
            alert_hash_base = f"debt_alert_{debt['id']}_{due_date_dt.strftime('%Y-%m-%d')}" # Use formatted date for hash
            alert_hash = hashlib.md5(alert_hash_base.encode()).hexdigest()

            if alert_hash not in dismissed_alerts_hashes:
                generated_alerts.append({
                    "type": alert_type,
                    "message": message,
                    "icon": icon,
                    "alert_hash": alert_hash,
                    "is_read": False
                })


    # 3. Savings Goal Progress Alerts
    for goal in metrics["savings_goals"]:
        message = None
        alert_type = None
        icon = None
        savings_tier = "initial"

        # Check if target_amount is valid and positive before comparison
        if goal['target_amount'] is None or goal['target_amount'] <= 0:
            savings_tier = "no_target"
        elif goal['current_amount'] >= goal['target_amount']:
            savings_tier = "smashed"
        elif goal['progress_percentage'] >= 75:
            savings_tier = "75_percent"
        elif goal['progress_percentage'] >= 25:
            savings_tier = "25_percent"
        elif goal['current_amount'] > 0 and goal['progress_percentage'] < 25:
             savings_tier = "initial_progress"


        if savings_tier == "smashed":
            message = f"Fantastic! You've **smashed your {goal['goal']} goal**! Consider setting a new one!"
            alert_type = "success"
            icon = "fas fa-trophy"
        elif savings_tier == "75_percent":
            message = f"Almost there! Your **{goal['goal']} goal is {goal['progress_percentage']:.0f}% complete**. Keep pushing!"
            alert_type = "info"
            icon = "fas fa-star"
        elif savings_tier == "25_percent":
            message = f"Good progress on **{goal['goal']}!** You're at **{goal['progress_percentage']:.0f}%** of your target."
            alert_type = "info"
            icon = "fas fa-piggy-bank"
        elif savings_tier == "initial_progress":
            message = f"Great start on your **{goal['goal']} goal**! You've already saved **${goal['current_amount']:.2f}**. Keep going!"
            alert_type = "info"
            icon = "fas fa-seedling"
        elif savings_tier == "no_target":
            message = f"Your savings goal '{goal['goal']}' doesn't have a target amount. Set one to track your progress!"
            alert_type = "info"
            icon = "fas fa-clipboard-list"

        if message:
            alert_hash_base = f"savings_alert_{goal['id']}_{savings_tier}"
            alert_hash = hashlib.md5(alert_hash_base.encode()).hexdigest()

            if alert_hash not in dismissed_alerts_hashes:
                generated_alerts.append({
                    "type": alert_type,
                    "message": message,
                    "icon": icon,
                    "alert_hash": alert_hash,
                    "is_read": False
                })


    # 4. Cash Flow Health Alerts
    message = None
    alert_type = None
    icon = None
    cash_flow_tier = "healthy"
    if metrics["cash_flow"] < 0:
        cash_flow_tier = "negative"
    elif metrics["cash_flow"] >= 0 and metrics["cash_flow"] < 100:
        cash_flow_tier = "tight"


    if cash_flow_tier == "negative":
        message = f"Warning! Your **net cash flow is negative (${abs(metrics['cash_flow']):.2f})**. Let's find ways to boost income or cut expenses."
        alert_type = "danger"
        icon = "fas fa-chart-line"
    elif cash_flow_tier == "tight":
        message = f"Your cash flow is a bit tight (**${metrics['cash_flow']:.2f}**). Small changes can make a big difference!"
        alert_type = "warning"
        icon = "fas fa-chart-bar"
    elif cash_flow_tier == "healthy":
        message = f"Excellent cash flow! You're adding **${metrics['cash_flow']:.2f}** to your financial cushion. Keep it up!"
        alert_type = "success"
        icon = "fas fa-dollar-sign"


    if message:
        alert_hash_base = f"cash_flow_alert_{cash_flow_tier}_{today.strftime('%Y-%m')}"
        alert_hash = hashlib.md5(alert_hash_base.encode()).hexdigest()

        if alert_hash not in dismissed_alerts_hashes:
            generated_alerts.append({
                "type": alert_type,
                "message": message,
                "icon": icon,
                "alert_hash": alert_hash,
                "is_read": False
            })


    # 5. Emergency Fund Status Alerts
    message = None
    alert_type = None
    icon = None
    emergency_fund_target = metrics["average_monthly_expenses"] * 3
    emergency_fund_tier = "low" # Default if below 50%
    # Use metrics["total_assets"] as total_current_savings for this calculation as defined in _get_all_financial_metrics
    total_current_savings_for_ef = sum(g['current_amount'] for g in metrics["savings_goals"]) if metrics["savings_goals"] else 0.0

    if metrics["average_monthly_expenses"] > 0:
        if total_current_savings_for_ef >= emergency_fund_target:
            emergency_fund_tier = "strong"
        elif total_current_savings_for_ef >= emergency_fund_target * 0.5:
            emergency_fund_tier = "growing"
    else:
        emergency_fund_tier = "no_expense_data"

    if emergency_fund_tier == "strong":
        message = f"Your **emergency fund is strong**! You have at least 3 months of expenses covered. Financial security unlocked!"
        alert_type = "success"
        icon = "fas fa-shield-alt"
    elif emergency_fund_tier == "growing":
        # Ensure division by zero is handled if emergency_fund_target is 0
        progress_percent = (total_current_savings_for_ef / emergency_fund_target * 100) if emergency_fund_target > 0 else 0
        message = f"Your **emergency fund is growing**! You're at {round(progress_percent, 0):.0f}% of your 3-month target. Keep saving!"
        alert_type = "warning"
        icon = "fas fa-hand-holding-usd"
    elif emergency_fund_tier == "low":
        message = f"Focus on your **emergency fund**. It's currently below 50% of your 3-month target (${emergency_fund_target:.2f})."
        alert_type = "danger"
        icon = "fas fa-fire"
    elif emergency_fund_tier == "no_expense_data":
        message = "To assess your emergency fund, please record some expenses first. Then we can calculate your target!"
        alert_type = "info"
        icon = "fas fa-clipboard"

    if message:
        alert_hash_base = f"emergency_fund_alert_{emergency_fund_tier}"
        alert_hash = hashlib.md5(alert_hash_base.encode()).hexdigest()

        if alert_hash not in dismissed_alerts_hashes:
            generated_alerts.append({
                "type": alert_type,
                "message": message,
                "icon": icon,
                "alert_hash": alert_hash,
                "is_read": False
            })

    # 6. High Debt Alert
    message = None
    alert_type = None
    icon = None
    HIGH_DEBT_THRESHOLD_WARNING = 5000 # Example
    HIGH_DEBT_THRESHOLD_DANGER = 15000 # Example

    debt_tier = "low_or_none"
    if metrics["total_liabilities"] > HIGH_DEBT_THRESHOLD_DANGER:
        debt_tier = "critical"
    elif metrics["total_liabilities"] > HIGH_DEBT_THRESHOLD_WARNING:
        debt_tier = "warning"
    elif metrics["total_liabilities"] == 0 and metrics["all_total_income"] > 0:
        debt_tier = "debt_free"

    if debt_tier == "critical":
        message = f"Critical Debt Alert! Your total liabilities are **${metrics['total_liabilities']:.2f}**. Let's strategize a robust repayment plan!"
        alert_type = "danger"
        icon = "fas fa-hand-holding-dollar"
    elif debt_tier == "warning":
        message = f"Your total debt is **${metrics['total_liabilities']:.2f}**. It's manageable, but keeping an eye on it is key!"
        alert_type = "warning"
        icon = "fas fa-chart-pie"
    elif debt_tier == "debt_free":
        message = "Congratulations! You are **debt-free**! That's a huge financial win!"
        alert_type = "success"
        icon = "fas fa-check-double"

    if message:
        alert_hash_base = f"debt_status_alert_{debt_tier}"
        alert_hash = hashlib.md5(alert_hash_base.encode()).hexdigest()

        if alert_hash not in dismissed_alerts_hashes:
            generated_alerts.append({
                "type": alert_type,
                "message": message,
                "icon": icon,
                "alert_hash": alert_hash,
                "is_read": False
            })

    # Add a general financial health summary (only if other specific alerts exist and not dismissed)
    # The original logic checks `if generated_alerts` before adding this general one.
    # We'll adjust it slightly to always show it if data exists and not dismissed.
    general_health_message = f"Your overall financial health score is **{metrics['financial_health_score']}/100**. Click 'View Savings & Financial Health Overview' for details!"
    health_score_tier = "general_info"
    alert_hash_base_general = f"financial_health_summary_alert_{health_score_tier}"
    alert_hash_general = hashlib.md5(alert_hash_base_general.encode()).hexdigest()

    # Only add this if there is some financial data processed (not the "no data recorded yet" case)
    # and it hasn't been dismissed.
    if metrics["financial_health_score"] > 0 and alert_hash_general not in dismissed_alerts_hashes:
        generated_alerts.append({
            "type": "info",
            "message": general_health_message,
            "icon": "fas fa-heartbeat",
            "alert_hash": alert_hash_general,
            "is_read": False
        })


    # Sort alerts (e.g., critical first, then warnings, then info/success)
    type_order = {"danger": 1, "warning": 2, "info": 3, "success": 4}
    generated_alerts.sort(key=lambda x: type_order.get(x["type"], 99))

    # If no active alerts were generated at all (after filtering dismissed ones AND adding general info),
    # then show the "no alerts for now" message.
    # This ensures "no alerts" message only appears if truly nothing else is relevant.
    if not generated_alerts:
        message = "You have no alerts for now."
        alert_hash = hashlib.md5("no_alerts_message".encode()).hexdigest()
        generated_alerts.append({
            "type": "info",
            "message": message,
            "icon": "fas fa-check-circle",
            "alert_hash": alert_hash,
            "is_read": False
        })

    return generated_alerts

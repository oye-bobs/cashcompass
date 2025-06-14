import os
import calendar
from cs50 import SQL
from datetime import datetime, timedelta
from flask import Flask, render_template, session, request, redirect, url_for, flash
from flask_session import Session
from helpers import apology, login_required
import json
from werkzeug.security import check_password_hash, generate_password_hash


# Configure application
app = Flask(__name__)


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///budget.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.template_filter('to_datetime')
def to_datetime_filter(s, fmt='%Y-%m-%d %H:%M:%S'):
    """Converts a string to a datetime object."""
    try:
        return datetime.strptime(s, fmt)
    except (ValueError, TypeError):
        return None  # Or handle error as appropriate


@app.template_filter('date_format')
def date_format_filter(dt, fmt):
    """Formats a datetime object to a string."""
    if isinstance(dt, datetime):
        return dt.strftime(fmt)
    return dt  # Return original if not a datetime object (e.g., if it's already 'N/A')


@app.route("/")
@login_required
def dashboard():
    """Display user's financial dashboard"""
    user_id = session["user_id"]  # Or current_user.id

    # Get selected month from query parameter, default to current month
    selected_month = request.args.get('month', datetime.now().strftime('%Y-%m'))

    # Calculate display format for selected month
    selected_month_display = datetime.strptime(selected_month, '%Y-%m').strftime('%B %Y')

    # Generate list of available months for the dropdown (e.g., last 12 months)
    available_months = []
    current_date = datetime.now()
    for i in range(12):  # Generate for current month and last 11 months
        # Calculate the month by going back 'i' months
        year = current_date.year
        month = current_date.month - i
        if month <= 0:
            month += 12
            year -= 1

        # Create a datetime object for the first day of that month
        month_start_date = datetime(year, month, 1)

        month_val = month_start_date.strftime('%Y-%m')
        month_label = month_start_date.strftime('%B %Y')
        available_months.append((month_val, month_label))
    available_months.reverse()  # Show in chronological order

    # 1. Fetch Total Income for selected month
    income_items = db.execute("""
        SELECT amount
        FROM income
        WHERE user_id = ? AND strftime('%Y-%m', date) = ?
    """, user_id, selected_month)
    total_income = sum(item['amount'] for item in income_items) if income_items else 0

    # 2. Fetch Total Expenses for selected month
    expenses_items = db.execute("""
        SELECT amount
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', date) = ?
    """, user_id, selected_month)
    total_expenses = sum(item['amount'] for item in expenses_items) if expenses_items else 0

    # 3. Fetch Total Budget for selected month
    # Assuming 'date' column now exists in budget table and is used for monthly budgeting.
    budget_items_monthly = db.execute("""
        SELECT amount
        FROM budget
        WHERE user_id = ? AND strftime('%Y-%m', date) = ?
    """, user_id, selected_month)
    total_budget = sum(item['amount']
                       for item in budget_items_monthly) if budget_items_monthly else 0

    # 4. Fetch Total Savings for selected month (UPDATED: now filtered by month)
    savings_items = db.execute("""
        SELECT amount
        FROM savings
        WHERE user_id = ? AND strftime('%Y-%m', date) = ?
    """, user_id, selected_month)
    total_savings = sum(item['amount'] for item in savings_items) if savings_items else 0

    # 5. Calculate Net Balance for selected month
    net_balance = total_income - total_expenses

    # 6. Budget vs. Actual Spending per Category (Filtered by selected_month for *expenses*)
    budget_vs_actual = {}

    # Get categories that have expenses in the selected month
    # This now drives which categories appear in the bar chart
    relevant_expense_categories = db.execute("""
        SELECT DISTINCT category
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', date) = ?
    """, user_id, selected_month)

    # If there are no expenses for the selected month, the chart data will be empty
    if not relevant_expense_categories:
        budget_bar_labels = []
        budgeted_data = []
        spent_data = []
    else:
        for cat_entry in relevant_expense_categories:
            category = cat_entry['category']

            # Fetch the budgeted amount for this category for the SELECTED MONTH
            # Assuming budget table now allows monthly budgets via its 'date' column
            budgeted_amount_result = db.execute("""
                SELECT amount FROM budget WHERE user_id = ? AND category = ? AND strftime('%Y-%m', date) = ?
            """, user_id, category, selected_month)
            budgeted_amount = budgeted_amount_result[0]['amount'] if budgeted_amount_result and budgeted_amount_result[0]['amount'] else 0

            # Fetch the spent amount for this category in the selected month
            spent_amount_result = db.execute("""
                SELECT SUM(amount) AS spent FROM expenses WHERE user_id = ? AND category = ? AND strftime('%Y-%m', date) = ?
            """, user_id, category, selected_month)
            spent_amount = spent_amount_result[0]['spent'] if spent_amount_result and spent_amount_result[0]['spent'] else 0

            budget_vs_actual[category] = {
                "budgeted": budgeted_amount,
                "spent": spent_amount,
                "remaining": budgeted_amount - spent_amount
            }

        budget_bar_labels = [c for c in budget_vs_actual.keys()]
        budgeted_data = [d['budgeted'] for d in budget_vs_actual.values()]
        spent_data = [d['spent'] for d in budget_vs_actual.values()]

    # 7. Top Spending Categories (for Pie Chart) (Filtered by selected_month)
    top_expenses_by_category = db.execute("""
        SELECT category, SUM(amount) AS total_spent
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', date) = ?
        GROUP BY category
        ORDER BY total_spent DESC
        LIMIT 5
    """, user_id, selected_month)

    pie_chart_labels = [item['category'] for item in top_expenses_by_category]
    pie_chart_data = [item['total_spent'] for item in top_expenses_by_category]

    # 8. Daily Income vs. Expenses (for Line Chart) for the selected month
    # Fetch income data by day for the selected month
    daily_income_raw = db.execute("""
        SELECT
            strftime('%Y-%m-%d', date) AS day,
            SUM(amount) AS total_income
        FROM income
        WHERE user_id = ? AND strftime('%Y-%m', date) = ?
        GROUP BY day
        ORDER BY day
    """, user_id, selected_month)

    print("DEBUG: daily_income_raw =", daily_income_raw)  # DEBUG PRINT

    # Fetch expenses data by day for the selected month
    daily_expenses_raw = db.execute("""
        SELECT
            strftime('%Y-%m-%d', date) AS day,
            SUM(amount) AS total_expenses
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', date) = ?
        GROUP BY day
        ORDER BY day
    """, user_id, selected_month)

    print("DEBUG: daily_expenses_raw =", daily_expenses_raw)  # DEBUG PRINT

    # Calculate total income for the selected month
    monthly_income_total_result = db.execute("""
        SELECT SUM(amount) AS total
        FROM income
        WHERE user_id = ? AND strftime('%Y-%m', date) = ?
    """, user_id, selected_month)
    monthly_income_total = monthly_income_total_result[0][
        'total'] if monthly_income_total_result and monthly_income_total_result[0]['total'] else 0

    # Calculate total expenses for the selected month
    monthly_expenses_total_result = db.execute("""
        SELECT SUM(amount) AS total
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', date) = ?
    """, user_id, selected_month)
    monthly_expenses_total = monthly_expenses_total_result[0][
        'total'] if monthly_expenses_total_result and monthly_expenses_total_result[0]['total'] else 0

    # Combine daily data
    daily_data = {}

    # Get number of days in the selected month
    year, month = map(int, selected_month.split('-'))
    num_days_in_month = calendar.monthrange(year, month)[1]
    first_day_of_selected_month = datetime(year, month, 1)

    # Initialize all days of the selected month with zero income/expenses
    for i in range(num_days_in_month):
        current_day = first_day_of_selected_month + timedelta(days=i)
        formatted_date = current_day.strftime('%Y-%m-%d')
        daily_data[formatted_date] = {'income': 0, 'expenses': 0}

    for row in daily_income_raw:
        daily_data[row['day']]['income'] = row['total_income']
    for row in daily_expenses_raw:
        daily_data[row['day']]['expenses'] = row['total_expenses']

    print("DEBUG: daily_data after combining =", daily_data)  # DEBUG PRINT

    # Sort days chronologically (important after initializing all days)
    sorted_days = sorted(daily_data.keys())
    line_chart_labels = []
    line_chart_income_data = []
    line_chart_expenses_data = []

    for day in sorted_days:
        line_chart_labels.append(datetime.strptime(
            day, '%Y-%m-%d').strftime('%b %d'))  # Format to 'Jun 01'
        line_chart_income_data.append(daily_data[day]['income'])
        line_chart_expenses_data.append(daily_data[day]['expenses'])

    print("DEBUG: final line_chart_labels =", line_chart_labels)  # DEBUG PRINT
    print("DEBUG: final line_chart_income_data =", line_chart_income_data)  # DEBUG PRINT
    print("DEBUG: final line_chart_expenses_data =", line_chart_expenses_data)  # DEBUG PRINT

    return render_template("index.html",  # Changed from "dashboard.html" to "index.html"
                           total_income=total_income,
                           total_expenses=total_expenses,
                           total_budget=total_budget,
                           total_savings=total_savings,
                           net_balance=net_balance,
                           budget_vs_actual=budget_vs_actual,
                           budget_bar_labels=budget_bar_labels,
                           budgeted_data=budgeted_data,
                           spent_data=spent_data,
                           pie_chart_labels=pie_chart_labels,
                           pie_chart_data=pie_chart_data,
                           line_chart_labels=line_chart_labels,
                           line_chart_income_data=line_chart_income_data,
                           line_chart_expenses_data=line_chart_expenses_data,
                           selected_month=selected_month,  # Pass selected month
                           selected_month_display=selected_month_display,  # Pass display format
                           available_months=available_months,  # Pass list of months
                           monthly_income_total=monthly_income_total,  # New: Pass monthly total income
                           monthly_expenses_total=monthly_expenses_total)  # New: Pass monthly total expenses


@app.route("/savings_dashboard")
@login_required
def savings_dashboard():
    """Display user's savings goals, net worth, and financial health score"""
    user_id = session["user_id"]

    # --- Savings Goal Tracker ---
    # Fetch all savings goals, now explicitly selecting 'target_amount'
    savings_goals_raw = db.execute("""
        SELECT id, goal, amount, target_amount FROM savings WHERE user_id = ?
    """, user_id)

    savings_goals = []
    if savings_goals_raw:
        for item in savings_goals_raw:
            current_amount = item['amount']
            target_amount = item['target_amount']  # Use the fetched target_amount

            # Ensure target_amount is not zero or None to avoid division by zero
            if target_amount is None or target_amount <= 0:
                # Handle cases where target_amount might be missing or invalid
                # For display, set to 0% if target is invalid/not set
                progress_percentage = 0
            else:
                progress_percentage = (current_amount / target_amount * 100)
                progress_percentage = min(progress_percentage, 100)  # Cap at 100%

            savings_goals.append({
                "id": item['id'],
                "goal": item['goal'],
                "current_amount": current_amount,
                "target_amount": target_amount,
                "progress_percentage": round(progress_percentage, 2)
            })

    # --- Financial Data for Cash Flow ---
    # Fetch total income and expenses (all time) for Cash Flow and Financial Health Score
    all_income_items = db.execute("SELECT amount FROM income WHERE user_id = ?", user_id)
    all_total_income = sum(item['amount'] for item in all_income_items) if all_income_items else 0

    all_expenses_items = db.execute("SELECT amount FROM expenses WHERE user_id = ?", user_id)
    all_total_expenses = sum(item['amount']
                             for item in all_expenses_items) if all_expenses_items else 0

    # Calculate Cash Flow (Income - Expenses)
    cash_flow = all_total_income - all_total_expenses

    # --- Net Worth Tracker (Traditional: Assets - Liabilities) ---
    # Total Assets: For this example, we'll use sum of all savings as a proxy for liquid assets.
    # In a real application, you'd query a dedicated 'assets' table (e.g., bank accounts, investments).
    total_assets = sum(goal['current_amount'] for goal in savings_goals) if savings_goals else 0
    # You can add other assets here if you create an 'assets' table:
    # other_assets_result = db.execute("SELECT SUM(value) FROM assets WHERE user_id = ?", user_id)
    # total_assets += other_assets_result[0]['SUM(value)'] if other_assets_result and other_assets_result[0]['SUM(value)'] else 0

    # Total Liabilities: NOW querying the new 'debt' table
    total_liabilities_result = db.execute("""
        SELECT SUM(current_balance) AS total_debt FROM debt WHERE user_id = ?
    """, user_id)
    total_liabilities = total_liabilities_result[0][
        'total_debt'] if total_liabilities_result and total_liabilities_result[0]['total_debt'] is not None else 0.0

    net_worth = total_assets - total_liabilities

    # --- Financial Health Score ---
    financial_health_score = 0
    score_details = []

    # Re-use total_current_savings which is the sum of 'amount' from savings goals
    total_current_savings = sum(goal['current_amount']
                                for goal in savings_goals) if savings_goals else 0

    # 1. Savings Rate (based on all-time income and total current savings)
    savings_rate = (total_current_savings / all_total_income * 100) if all_total_income > 0 else 0
    savings_rate_score = 0
    if savings_rate >= 20:  # Excellent savings
        savings_rate_score = 40
    elif savings_rate >= 10:  # Good savings
        savings_rate_score = 25
    else:  # Low savings
        savings_rate_score = 10
    financial_health_score += savings_rate_score
    score_details.append(f"Savings Rate: {round(savings_rate, 2)}% ({savings_rate_score} points)")

    # 2. Debt-to-Asset Ratio (lower is better)
    # Now uses the actual total_liabilities fetched from the debt table
    debt_to_asset_ratio = (total_liabilities / total_assets * 100) if total_assets > 0 else 0
    debt_score = 0
    if total_liabilities == 0:  # No debt
        debt_score = 30
    elif debt_to_asset_ratio <= 30:  # Low debt
        debt_score = 30
    elif debt_to_asset_ratio <= 60:  # Moderate debt
        debt_score = 15
    else:  # High debt
        debt_score = 5
    financial_health_score += debt_score
    # Include total debt in detail
    score_details.append(
        f"Debt-to-Asset Ratio: {round(debt_to_asset_ratio, 2)}% ({debt_score} points) - Total Debt: ${total_liabilities:.2f}")

    # 3. Emergency Fund (assuming an ideal target like 3-6 months of expenses)
    num_months_expenses_result = db.execute(
        "SELECT COUNT(DISTINCT strftime('%Y-%m', date)) AS num_months FROM expenses WHERE user_id = ?", user_id)
    num_months_expenses = num_months_expenses_result[0][
        'num_months'] if num_months_expenses_result and num_months_expenses_result[0]['num_months'] else 1

    average_monthly_expenses = (
        all_total_expenses / num_months_expenses) if num_months_expenses > 0 else 0
    emergency_fund_target = average_monthly_expenses * 3  # 3 months coverage

    emergency_fund_score = 0
    # Using total_assets (current savings) for emergency fund check
    if total_assets >= emergency_fund_target:
        emergency_fund_score = 30
    elif total_assets >= emergency_fund_target * 0.5:
        emergency_fund_score = 15
    else:
        emergency_fund_score = 5
    financial_health_score += emergency_fund_score
    score_details.append(
        f"Emergency Fund Coverage (vs 3 months avg expenses ${average_monthly_expenses:.2f}): ${total_current_savings:.2f} ({emergency_fund_score} points)")

    # Cap the total score (e.g., out of 100)
    financial_health_score = min(financial_health_score, 100)

    return render_template("savings_dashboard.html",
                           savings_goals=savings_goals,
                           net_worth=net_worth,  # Now represents Assets - Liabilities
                           cash_flow=cash_flow,  # Total Income - Total Expenses
                           financial_health_score=financial_health_score,
                           score_details=score_details)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["password_hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Validate input fields
        if not username:
            return apology("must provide username", 400)
        if not password:
            return apology("must provide password", 400)
        if not confirmation:
            return apology("must confirm password", 400)
        if password != confirmation:
            return apology("passwords do not match", 400)

        # Hash the password
        hash_pass = generate_password_hash(password)

        # Try to insert the user into the database
        try:
            # The 'users' table has 'created_at' which has a DEFAULT value
            db.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                username,
                hash_pass
            )
        except ValueError:  # This might be OperationalError or IntegrityError in real DBs
            return apology("username already exists", 400)

        # Redirect to login or homepage after successful registration
        flash("Successfully registered! Please log in.")
        return redirect("/login")

    else:
        return render_template("register.html")


@app.route("/budget", methods=["GET", "POST"])
@login_required
def budget():
    """Manage budget"""
    user_id = session["user_id"]  # Or current_user.id if using Flask-Login's current_user

    if request.method == "POST":
        category = request.form.get("category")
        amount = request.form.get("amount")
        budget_month_str = request.form.get("month")  # Get the selected month from the form

        # Validate inputs
        if not category:
            flash("Category cannot be empty", "danger")
            return redirect("/budget")
        try:
            amount = float(amount)
            if amount <= 0:
                flash("Amount must be a positive number", "danger")
                return redirect("/budget")
        except (ValueError, TypeError):
            flash("Invalid amount format", "danger")
            return redirect("/budget")

        # Validate and format the month input
        try:
            # Parse as YYYY-MM and then convert to first day of the month
            budget_date = datetime.strptime(budget_month_str, '%Y-%m').replace(day=1)
        except ValueError:
            flash("Invalid month format provided.", "danger")
            return redirect("/budget")

        # Insert the budget item into the database, including the date
        db.execute("""
            INSERT INTO budget (user_id, category, amount, date)
            VALUES (?, ?, ?, ?)
        """, user_id, category, amount, budget_date.strftime('%Y-%m-%d %H:%M:%S'))  # Store as full timestamp

        flash("Budget item added successfully!", "success")
        return redirect("/budget")

    else:
        # GET request: Retrieve budget items for the current user
        selected_month = request.args.get('month', datetime.now().strftime('%Y-%m'))
        selected_month_display = datetime.strptime(selected_month, '%Y-%m').strftime('%B %Y')
        current_month_iso = datetime.now().strftime('%Y-%m')  # For setting default on 'add' form

        available_months = []
        current_date_for_dropdown = datetime.now()
        for i in range(12):  # Generate for current month and last 11 months
            year = current_date_for_dropdown.year
            month = current_date_for_dropdown.month - i
            if month <= 0:
                month += 12
                year -= 1
            month_start_date = datetime(year, month, 1)
            month_val = month_start_date.strftime('%Y-%m')
            month_label = month_start_date.strftime('%B %Y')
            available_months.append((month_val, month_label))
        available_months.reverse()  # Show in chronological order

        # Fetch budget items for the selected month only
        budget_items = db.execute("""
            SELECT id, category, amount, date
            FROM budget
            WHERE user_id = ? AND strftime('%Y-%m', date) = ?
            ORDER BY category
        """, user_id, selected_month)

        # Calculate total budget for the selected month
        total_budget = sum(item['amount'] for item in budget_items) if budget_items else 0

        return render_template("budget.html",
                               budget_items=budget_items,
                               total_budget=total_budget,
                               selected_month=selected_month,
                               selected_month_display=selected_month_display,
                               available_months=available_months,
                               current_month_iso=current_month_iso)  # Pass default for add form

# Add your new edit and delete routes as well


@app.route("/budget/edit/<int:item_id>", methods=["POST"])
@login_required
def edit_budget(item_id):
    """Edit a budget item"""
    user_id = session["user_id"]  # Or current_user.id

    category = request.form.get("category")
    amount = request.form.get("amount")
    date_str = request.form.get("date")  # Get date from edit form

    if not category:
        flash("Category cannot be empty", "danger")
        return redirect("/budget")
    try:
        amount = float(amount)
        if amount <= 0:
            flash("Amount must be a positive number", "danger")
            return redirect("/budget")
    except (ValueError, TypeError):
        flash("Invalid amount format", "danger")
        return redirect("/budget")

    # Validate and format the date input
    try:
        budget_date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        flash("Invalid date format provided.", "danger")
        return redirect("/budget")

    # Update the budget item in the database, including the date
    db.execute("""
        UPDATE budget
        SET category = ?, amount = ?, date = ?
        WHERE id = ? AND user_id = ?
    """, category, amount, budget_date.strftime('%Y-%m-%d %H:%M:%S'), item_id, user_id)

    flash("Budget item updated successfully!", "success")
    return redirect("/budget")


@app.route("/budget/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_budget(item_id):
    """Delete a budget item"""
    user_id = session["user_id"]  # Or current_user.id

    # Delete the budget item from the database
    db.execute("""
        DELETE FROM budget
        WHERE id = ? AND user_id = ?
    """, item_id, user_id)

    flash("Budget item deleted successfully!", "success")
    return redirect("/budget")


@app.route("/expenses", methods=["GET", "POST"])
@login_required
def expenses():
    """Manage expenses"""
    user_id = session["user_id"]

    # Month selection logic (copied from dashboard route)
    current_year = datetime.now().year
    current_month = datetime.now().month

    selected_month_str = request.args.get("month")
    if selected_month_str:
        try:
            selected_month_year = datetime.strptime(selected_month_str, "%Y-%m")
            selected_year = selected_month_year.year
            selected_month_num = selected_month_year.month
        except ValueError:
            # Fallback if invalid month string is provided
            selected_year = current_year
            selected_month_num = current_month
            selected_month_str = f"{selected_year}-{selected_month_num:02d}"
    else:
        selected_year = current_year
        selected_month_num = current_month
        selected_month_str = f"{selected_year}-{selected_month_num:02d}"

    selected_month_display = calendar.month_name[selected_month_num] + " " + str(selected_year)

    available_months = []
    # Generate available months for dropdown (e.g., last 12 months plus current)
    for i in range(12):  # Last 12 months from current
        month_date = datetime(current_year, current_month, 1) - timedelta(days=30 * i)
        available_months.append((month_date.strftime("%Y-%m"), month_date.strftime("%B %Y")))
    available_months.reverse()  # Show chronologically
    available_months.append((datetime.now().strftime(
        "%Y-%m"), datetime.now().strftime("%B %Y") + " (Current)"))

    if request.method == "POST":
        category = request.form.get("category")
        amount = request.form.get("amount")
        # Assuming you also add a 'date' field to the expense form for flexibility
        date_str = request.form.get("date")

        # Basic validation for expenses
        if not category or not amount or not date_str:
            flash("Missing required expense information: Category, Amount, or Date.", "danger")
            return redirect("/expenses")

        try:
            amount = float(amount)
            if amount <= 0:
                flash("Amount must be a positive number.", "danger")
                return redirect("/expenses")
            # Validate date format
            datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            flash("Invalid amount or date format.", "danger")
            return redirect("/expenses")

        # Insert the expense item, including the date
        db.execute("""
            INSERT INTO expenses (user_id, category, amount, date)
            VALUES (?, ?, ?, ?)
        """, user_id, category, amount, date_str)

        flash("Expense added successfully!", "success")
        # Redirect to current month view
        return redirect(url_for("expenses", month=selected_month_str))

    else:  # GET request
        # Get categories from budget for the dropdown (only allows budgeted categories)
        budget_categories = db.execute("""
            SELECT category
            FROM budget
            WHERE user_id = ?
            GROUP BY category
            ORDER BY category
        """, user_id)
        categories = [row["category"] for row in budget_categories]

        # Get expenses for the current user, FILTERED BY SELECTED MONTH
        expenses_items = db.execute("""
            SELECT id, category, amount, date
            FROM expenses
            WHERE user_id = ? AND strftime('%Y-%m', date) = ?
            ORDER BY date DESC, category
        """, user_id, selected_month_str)

        # Calculate total expenses for the selected month
        total_expenses = sum(item['amount'] for item in expenses_items)

        return render_template("expenses.html",
                               categories=categories,
                               expenses_items=expenses_items,
                               total_expenses=total_expenses,
                               available_months=available_months,  # Pass to template
                               selected_month=selected_month_str,  # Pass to template
                               selected_month_display=selected_month_display  # Pass to template
                               )


@app.route("/expenses/edit/<int:item_id>", methods=["POST"])
@login_required
def edit_expense(item_id):
    """Edit an expense item"""
    user_id = session["user_id"]

    category = request.form.get("category")
    amount = request.form.get("amount")
    date_str = request.form.get("date")  # Get date for editing as well

    if not category or not amount or not date_str:
        flash("Missing required expense information.", "danger")
        return redirect("/expenses")
    try:
        amount = float(amount)
        if amount <= 0:
            flash("Amount must be a positive number.", "danger")
            return redirect("/expenses")
        datetime.strptime(date_str, "%Y-%m-%d")  # Validate date format
    except (ValueError, TypeError):
        flash("Invalid amount or date format.", "danger")
        return redirect("/expenses")

    db.execute("""
        UPDATE expenses
        SET category = ?, amount = ?, date = ?
        WHERE id = ? AND user_id = ?
    """, category, amount, date_str, item_id, user_id)

    flash("Expense item updated successfully!", "success")
    # Redirect to the expenses page, attempting to preserve the current month view
    selected_month_str = request.args.get("month")  # Try to get month from URL if available
    return redirect(url_for("expenses", month=selected_month_str if selected_month_str else datetime.now().strftime("%Y-%m")))


@app.route("/expenses/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_expense(item_id):
    """Delete an expense item"""
    user_id = session["user_id"]

    db.execute("""
        DELETE FROM expenses
        WHERE id = ? AND user_id = ?
    """, item_id, user_id)

    flash("Expense item deleted successfully!", "success")
    # Redirect to the expenses page, attempting to preserve the current month view
    selected_month_str = request.args.get("month")  # Try to get month from URL if available
    return redirect(url_for("expenses", month=selected_month_str if selected_month_str else datetime.now().strftime("%Y-%m")))


@app.route("/income", methods=["GET", "POST"])
@login_required
def income():
    """Manage income"""
    user_id = session["user_id"]  # Or current_user.id if using Flask-Login's current_user

    if request.method == "POST":
        source = request.form.get("source")
        amount = request.form.get("amount")
        income_date_str = request.form.get("date")  # Get the date from the form

        # Validate inputs
        if not source:
            flash("Income source cannot be empty", "danger")
            return redirect("/income")
        try:
            amount = float(amount)
            if amount <= 0:
                flash("Amount must be a positive number", "danger")
                return redirect("/income")
        except (ValueError, TypeError):
            flash("Invalid amount format", "danger")
            return redirect("/income")

        # Validate and format the date input
        try:
            income_date = datetime.strptime(income_date_str, '%Y-%m-%d')
        except ValueError:
            flash("Invalid date format provided.", "danger")
            return redirect("/income")

        # Insert the income item into the database, including the date
        db.execute("""
            INSERT INTO income (user_id, source, amount, date)
            VALUES (?, ?, ?, ?)
        """, user_id, source, amount, income_date.strftime('%Y-%m-%d %H:%M:%S'))

        flash("Income added successfully!", "success")
        return redirect("/income")

    else:
        # GET request: Retrieve income items for the current user
        selected_month = request.args.get('month', datetime.now().strftime('%Y-%m'))
        selected_month_display = datetime.strptime(selected_month, '%Y-%m').strftime('%B %Y')
        current_date_iso = datetime.now().strftime('%Y-%m-%d')  # For setting default on 'add' form

        available_months = []
        current_date_for_dropdown = datetime.now()
        for i in range(12):  # Generate for current month and last 11 months
            year = current_date_for_dropdown.year
            month = current_date_for_dropdown.month - i
            if month <= 0:
                month += 12
                year -= 1
            month_start_date = datetime(year, month, 1)
            month_val = month_start_date.strftime('%Y-%m')
            month_label = month_start_date.strftime('%B %Y')
            available_months.append((month_val, month_label))
        available_months.reverse()  # Show in chronological order

        # Fetch income items for the selected month only
        income_items = db.execute("""
            SELECT id, source, amount, date
            FROM income
            WHERE user_id = ? AND strftime('%Y-%m', date) = ?
            ORDER BY date DESC, source
        """, user_id, selected_month)

        # Calculate total income for the selected month
        total_income = sum(item['amount'] for item in income_items) if income_items else 0

        return render_template("income.html",
                               income_items=income_items,
                               total_income=total_income,
                               selected_month=selected_month,
                               selected_month_display=selected_month_display,
                               available_months=available_months,
                               current_date_iso=current_date_iso)


@app.route("/income/edit/<int:item_id>", methods=["POST"])
@login_required
def edit_income(item_id):
    """Edit an income item"""
    user_id = session["user_id"]  # Or current_user.id

    source = request.form.get("source")
    amount = request.form.get("amount")
    date_str = request.form.get("date")  # Get date from edit form

    if not source:
        flash("Income source cannot be empty", "danger")
        return redirect("/income")
    try:
        amount = float(amount)
        if amount <= 0:
            flash("Amount must be a positive number", "danger")
            return redirect("/income")
    except (ValueError, TypeError):
        flash("Invalid amount format", "danger")
        return redirect("/income")

    # Validate and format the date input
    try:
        income_date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        flash("Invalid date format provided.", "danger")
        return redirect("/income")

    # Update the income item in the database, including the date
    db.execute("""
        UPDATE income
        SET source = ?, amount = ?, date = ?
        WHERE id = ? AND user_id = ?
    """, source, amount, income_date.strftime('%Y-%m-%d %H:%M:%S'), item_id, user_id)

    flash("Income item updated successfully!", "success")
    return redirect("/income")


@app.route("/income/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_income(item_id):
    """Delete an income item"""
    user_id = session["user_id"]  # Or current_user.id

    db.execute("""
        DELETE FROM income
        WHERE id = ? AND user_id = ?
    """, item_id, user_id)

    flash("Income item deleted successfully!", "success")
    return redirect("/income")


@app.route("/savings", methods=["GET", "POST"])
@login_required
def savings():
    """Manage savings"""
    user_id = session["user_id"]  # Or current_user.id if using Flask-Login's current_user

    if request.method == "POST":
        goal = request.form.get("goal")
        amount = request.form.get("amount")
        target_amount = request.form.get("target_amount")  # Get target amount

        # Validate inputs
        if not goal:
            flash("Savings goal cannot be empty", "danger")
            return redirect("/savings")
        try:
            amount = float(amount)
            if amount < 0:  # Current amount can be 0 or more
                flash("Current amount saved must be a non-negative number", "danger")
                return redirect("/savings")
        except (ValueError, TypeError):
            flash("Invalid current amount format", "danger")
            return redirect("/savings")

        try:
            target_amount = float(target_amount)
            if target_amount <= 0:  # Target amount must be positive
                flash("Target amount must be a positive number", "danger")
                return redirect("/savings")
            if target_amount < amount:  # Target should ideally be greater than or equal to current
                flash("Target amount should not be less than current amount saved", "warning")
                # return redirect("/savings") # Optionally, you could prevent submission here
        except (ValueError, TypeError):
            flash("Invalid target amount format", "danger")
            return redirect("/savings")

        # Insert the savings item into the database, including target_amount
        db.execute("""
            INSERT INTO savings (user_id, goal, amount, target_amount)
            VALUES (?, ?, ?, ?)
        """, user_id, goal, amount, target_amount)

        flash("Savings goal added successfully!", "success")
        return redirect("/savings")

    else:
        # GET request: Retrieve ALL savings items for the current user
        # Select 'id', 'goal', 'amount', AND 'target_amount'
        savings_items = db.execute("""
            SELECT id, goal, amount, target_amount
            FROM savings
            WHERE user_id = ?
            ORDER BY goal
        """, user_id)

        # Calculate total current savings (sum of 'amount' only)
        total_current_savings = sum(item['amount']
                                    for item in savings_items) if savings_items else 0

        # No month-related variables are passed to the template for savings
        return render_template("savings.html",
                               savings_items=savings_items,
                               total_current_savings=total_current_savings)  # Pass this to the template


@app.route("/savings/edit/<int:item_id>", methods=["POST"])
@login_required
def edit_savings(item_id):
    """Edit a savings item"""
    user_id = session["user_id"]  # Or current_user.id

    goal = request.form.get("goal")
    amount = request.form.get("amount")
    target_amount = request.form.get("target_amount")  # Get target amount

    if not goal:
        flash("Savings goal cannot be empty", "danger")
        return redirect("/savings")
    try:
        amount = float(amount)
        if amount < 0:
            flash("Current amount saved must be a non-negative number", "danger")
            return redirect("/savings")
    except (ValueError, TypeError):
        flash("Invalid current amount format", "danger")
        return redirect("/savings")

    try:
        target_amount = float(target_amount)
        if target_amount <= 0:
            flash("Target amount must be a positive number", "danger")
            return redirect("/savings")
        if target_amount < amount:
            flash("Target amount should not be less than current amount saved", "warning")
            # return redirect("/savings") # Optionally, prevent submission
    except (ValueError, TypeError):
        flash("Invalid target amount format", "danger")
        return redirect("/savings")

    # Update the savings item in the database, including the new target_amount
    db.execute("""
        UPDATE savings
        SET goal = ?, amount = ?, target_amount = ?
        WHERE id = ? AND user_id = ?
    """, goal, amount, target_amount, item_id, user_id)

    flash("Savings item updated successfully!", "success")
    return redirect("/savings")


@app.route("/savings/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_savings(item_id):
    """Delete a savings item"""
    user_id = session["user_id"]  # Or current_user.id

    # Delete the savings item from the database
    db.execute("""
        DELETE FROM savings
        WHERE id = ? AND user_id = ?
    """, item_id, user_id)

    flash("Savings item deleted successfully!", "success")
    return redirect("/savings")


@app.route("/profile", methods=["GET", "POST"])
@login_required  # Ensure the user is logged in
def profile():
    """User profile management"""

    user_id = session["user_id"]

    # Fetch user details from the database
    # SELECT username, email, and created_at as per your 'users' table schema
    user_data = db.execute("""
        SELECT username, email, created_at
        FROM users
        WHERE id = ?
    """, user_id)

    # Check if user data was found
    if not user_data:
        flash("User profile not found. Please log in again.",
              "danger")  # Use flash for user feedback
        return redirect("/login")  # Redirect to login if user not found

    # db.execute returns a list of dictionaries/rows.
    # For a unique user_id, we expect a list with one item.
    user = user_data[0]

    # Render the profile.html template, passing the fetched user data
    return render_template("profile.html", user=user)


@app.route("/debt", methods=["GET", "POST"])
@login_required
def debt():
    """Manage debt records"""
    user_id = session["user_id"]

    if request.method == "POST":
        # Get data from form for adding/editing (simplified fields)
        debt_name = request.form.get("debt_name")
        debt_type = request.form.get("debt_type")
        current_balance = request.form.get("current_balance")
        due_date_str = request.form.get("due_date")

        # Basic validation for simplified fields
        if not debt_name or not debt_type or not current_balance:
            flash("Missing required debt information: Name, Type, or Current Balance.", "danger")
            return redirect("/debt")

        try:
            current_balance = float(current_balance)
            if current_balance < 0:
                flash("Current balance must be a non-negative number.", "danger")
                return redirect("/debt")
        except (ValueError, TypeError):
            flash("Invalid current balance format.", "danger")
            return redirect("/debt")

        # Date validation and formatting (store as YYYY-MM-DD strings or NULL)
        due_date = due_date_str if due_date_str else None

        # For the simplified form, other fields will use their DEFAULT values in the DB
        # or be NULL if not provided during table creation.
        # Ensure your SQL INSERT statement handles this by only specifying columns provided.
        db.execute("""
            INSERT INTO debt (user_id, debt_name, debt_type, current_balance, due_date)
            VALUES (?, ?, ?, ?, ?)
        """, user_id, debt_name, debt_type, current_balance, due_date)

        flash("Debt item added successfully!", "success")
        return redirect("/debt")

    else:  # GET request
        debt_items = db.execute("""
            SELECT id, debt_name, debt_type, original_amount, current_balance,
                   interest_rate, minimum_payment, due_date, start_date, end_date,
                   lender, notes
            FROM debt
            WHERE user_id = ?
            ORDER BY due_date ASC, debt_name ASC
        """, user_id)

        total_liabilities = sum(item['current_balance']
                                for item in debt_items) if debt_items else 0.0

        # Define common debt types for the dropdown
        debt_types = ["Credit Card", "Student Loan",
                      "Auto Loan", "Mortgage", "Personal Loan", "Other"]

        return render_template("debt.html",
                               debt_items=debt_items,
                               total_liabilities=total_liabilities,
                               debt_types=debt_types)


@app.route("/debt/edit/<int:item_id>", methods=["POST"])
@login_required
def edit_debt(item_id):
    """Edit a debt item"""
    user_id = session["user_id"]

    # Get data from form for editing (simplified fields)
    debt_name = request.form.get("debt_name")
    debt_type = request.form.get("debt_type")
    current_balance = request.form.get("current_balance")
    due_date_str = request.form.get("due_date")

    # Basic validation for simplified fields
    if not debt_name or not debt_type or not current_balance:
        flash("Missing required debt information: Name, Type, or Current Balance.", "danger")
        return redirect("/debt")

    try:
        current_balance = float(current_balance)
        if current_balance < 0:
            flash("Current balance must be a non-negative number.", "danger")
            return redirect("/debt")
    except (ValueError, TypeError):
        flash("Invalid current balance format.", "danger")
        return redirect("/debt")

    due_date = due_date_str if due_date_str else None

    # Update the debt item in the database (only simplified fields)
    db.execute("""
        UPDATE debt
        SET debt_name = ?, debt_type = ?, current_balance = ?, due_date = ?
        WHERE id = ? AND user_id = ?
    """, debt_name, debt_type, current_balance, due_date, item_id, user_id)

    flash("Debt item updated successfully!", "success")
    return redirect("/debt")


@app.route("/debt/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_debt(item_id):
    """Delete a debt item"""
    user_id = session["user_id"]

    db.execute("""
        DELETE FROM debt
        WHERE id = ? AND user_id = ?
    """, item_id, user_id)

    flash("Debt item deleted successfully!", "success")
    return redirect("/debt")


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """User settings management"""
    user_id = session["user_id"]

    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")

        # Fetch user's current password hash from DB
        user_row = db.execute("SELECT password_hash FROM users WHERE id = ?", user_id)
        if not user_row:
            flash("User not found.", "danger")
            return redirect("/login")  # Should not happen with @login_required

        # Validate current password
        if not current_password or not check_password_hash(user_row[0]["password_hash"], current_password):
            return apology("Invalid current password", 403)

        # Validate new password
        if not new_password or not confirmation:
            return apology("Must provide and confirm new password", 400)
        if new_password != confirmation:
            return apology("New passwords do not match", 400)
        if len(new_password) < 6:  # Example: add a minimum length
            return apology("New password must be at least 6 characters long", 400)

        # Hash the new password
        new_password_hash = generate_password_hash(new_password)

        # Update password in database
        db.execute("""
            UPDATE users
            SET password_hash = ?
            WHERE id = ?
        """, new_password_hash, user_id)

        flash("Password updated successfully!", "success")
        return redirect("/profile")  # Redirect to profile or settings page

    else:  # GET request
        # Fetch user details (username, email) to display in settings form
        user_data = db.execute("""
            SELECT username, email
            FROM users
            WHERE id = ?
        """, user_id)

        if not user_data:
            flash("User data not found for settings. Please log in again.", "danger")
            return redirect("/login")

        user = user_data[0]
        return render_template("settings.html", user=user)


@app.route("/profile/change_password")
@login_required
def profile_change_password_redirect():
    """Redirects to the settings page for password change."""
    return redirect("/settings")


@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    """Allow user to edit their profile information (e.g., username, email)"""
    user_id = session["user_id"]

    if request.method == "POST":
        new_username = request.form.get("username")
        new_email = request.form.get("email")

        # Basic validation for new username/email
        if not new_username:
            return apology("Username cannot be empty", 400)
        if not new_email:
            return apology("Email cannot be empty", 400)

        # Check if username already exists (excluding current user)
        existing_user = db.execute(
            "SELECT id FROM users WHERE username = ? AND id != ?", new_username, user_id)
        if existing_user:
            return apology("Username already taken", 400)

        # Update user's profile in the database
        db.execute("""
            UPDATE users
            SET username = ?, email = ?
            WHERE id = ?
        """, new_username, new_email, user_id)

        flash("Profile updated successfully!", "success")
        return redirect("/profile")

    else:  # GET request
        user_data = db.execute("SELECT username, email FROM users WHERE id = ?", user_id)
        if not user_data:
            flash("User data not found for profile editing. Please log in again.", "danger")
            return redirect("/login")
        user = user_data[0]
        return render_template("edit_profile.html", user=user)


@app.route("/profile/delete_account", methods=["GET", "POST"])
@login_required
def delete_account():
    """Allow user to delete their account after password confirmation."""
    user_id = session["user_id"]

    if request.method == "POST":
        password = request.form.get("password")

        # Fetch user's current password hash from DB
        user_row = db.execute("SELECT password_hash FROM users WHERE id = ?", user_id)
        if not user_row:
            flash("User not found.", "danger")
            return redirect("/login")  # Should not happen with @login_required

        # Validate submitted password
        if not password or not check_password_hash(user_row[0]["password_hash"], password):
            return apology("Invalid password", 403)  # Return apology for incorrect password

        # If password is correct, proceed with deletion
        # Delete user's budget entries
        db.execute("DELETE FROM budget WHERE user_id = ?", user_id)
        # Delete user's expense entries
        db.execute("DELETE FROM expenses WHERE user_id = ?", user_id)
        # Finally, delete the user from the users table
        db.execute("DELETE FROM users WHERE id = ?", user_id)

        # Clear the session after account deletion
        session.clear()
        flash("Your account has been successfully deleted.", "info")
        return redirect("/login")  # Redirect to login or a public confirmation page

    else:  # GET request, display confirmation page
        return render_template("delete_account.html")


# Changed to GET only as POST will be handled by JS for AI call
@app.route("/financial_advisor", methods=["GET"])
@login_required
def financial_advisor():
    """Provide AI-powered financial advice"""
    user_id = session["user_id"]

    # 1. Fetch Key Metrics from DB
    # Total Income (all time)
    all_income_result = db.execute(
        "SELECT SUM(amount) AS total_amount FROM income WHERE user_id = ?", user_id)
    total_income_all_time = all_income_result[0]['total_amount'] if all_income_result and all_income_result[0]['total_amount'] is not None else 0.0

    # Total Expenses (all time)
    all_expenses_result = db.execute(
        "SELECT SUM(amount) AS total_amount FROM expenses WHERE user_id = ?", user_id)
    total_expenses_all_time = all_expenses_result[0][
        'total_amount'] if all_expenses_result and all_expenses_result[0]['total_amount'] is not None else 0.0

    # Current Savings (sum of amounts in savings table)
    total_savings_result = db.execute(
        "SELECT SUM(amount) AS total_saved FROM savings WHERE user_id = ?", user_id)
    total_savings = total_savings_result[0]['total_saved'] if total_savings_result and total_savings_result[0]['total_saved'] is not None else 0.0

    # Total Debt (sum of current_balance in debt table)
    total_debt_result = db.execute(
        "SELECT SUM(current_balance) AS total_debt FROM debt WHERE user_id = ?", user_id)
    total_debt = total_debt_result[0]['total_debt'] if total_debt_result and total_debt_result[0]['total_debt'] is not None else 0.0

    # Net Worth (simplified: total_savings as assets - total_debt as liabilities)
    net_worth = total_savings - total_debt

    # Cash Flow (all-time income - expenses for overall advice)
    cash_flow = total_income_all_time - total_expenses_all_time

    # Emergency Fund Status (requires average monthly expenses)
    months_with_expenses_result = db.execute(
        "SELECT COUNT(DISTINCT strftime('%Y-%m', date)) AS num_months FROM expenses WHERE user_id = ?", user_id)
    num_months_with_expenses = months_with_expenses_result[0][
        'num_months'] if months_with_expenses_result and months_with_expenses_result[0]['num_months'] is not None else 1
    average_monthly_expenses = (total_expenses_all_time /
                                num_months_with_expenses) if num_months_with_expenses > 0 else 0.0
    emergency_fund_target_3_months = average_monthly_expenses * 3
    emergency_fund_coverage = total_savings / \
        average_monthly_expenses if average_monthly_expenses > 0 else 0.0

    # Budget adherence (current month over budget)
    current_month_str = datetime.now().strftime("%Y-%m")
    budget_categories_raw = db.execute("""
        SELECT category, amount AS budgeted_amount
        FROM budget
        WHERE user_id = ? AND strftime('%Y-%m', date) = ?
    """, user_id, current_month_str)
    actual_expenses_by_category_raw = db.execute("""
        SELECT category, SUM(amount) AS total_spent
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', date) = ?
        GROUP BY category
    """, user_id, current_month_str)

    budget_overview = {}
    for row in budget_categories_raw:
        budget_overview[row['category']] = {'budgeted': row['budgeted_amount'], 'spent': 0.0}
    for row in actual_expenses_by_category_raw:
        if row['category'] in budget_overview:
            budget_overview[row['category']]['spent'] = row['total_spent']
        else:  # Expense without a budget
            budget_overview[row['category']] = {'budgeted': 0.0, 'spent': row['total_spent']}

    over_budget_categories = []
    for category, data in budget_overview.items():
        if data['spent'] > data['budgeted']:
            over_budget_categories.append(
                f"{category} (Over by ${data['spent'] - data['budgeted']:.2f})")

    # Top Spending Categories (overall, for general advice)
    top_spending_raw = db.execute("""
        SELECT category, SUM(amount) AS total_spent
        FROM expenses
        WHERE user_id = ?
        GROUP BY category
        ORDER BY total_spent DESC
        LIMIT 3
    """, user_id)
    top_spending_categories_str = ", ".join(
        [f"{item['category']} (${item['total_spent']:.2f})" for item in top_spending_raw]) if top_spending_raw else "N/A"

    # Consolidate all financial data into a single dictionary to pass to JS
    financial_data = {
        "total_income_all_time": total_income_all_time,
        "total_expenses_all_time": total_expenses_all_time,
        "net_worth": net_worth,
        "cash_flow": cash_flow,
        "total_savings": total_savings,
        "total_debt": total_debt,
        "average_monthly_expenses": average_monthly_expenses,
        "emergency_fund_target_3_months": emergency_fund_target_3_months,
        "emergency_fund_coverage": emergency_fund_coverage,
        "over_budget_categories": over_budget_categories,
        "top_spending_categories_str": top_spending_categories_str
    }

    # Return data as JSON string to be picked up by frontend JS
    # The `json` module is imported at the top of the file.
    return render_template("financial_advisor.html", financial_data=json.dumps(financial_data))

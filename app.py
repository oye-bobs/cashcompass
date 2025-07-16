from dotenv import load_dotenv
import calendar
from datetime import datetime, timedelta, date
from flask import Flask, render_template, session, request, redirect, url_for, flash, jsonify
from flask_session import Session
from flask_mail import Mail, Message
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from helpers import apology, login_required, _get_all_financial_metrics, _generate_financial_alerts_list, execute_query_helper
import json
import markdown
import os
import requests
import traceback # Keep traceback for console logging

# NEW IMPORTS FOR SQLALCHEMY
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, func # text for raw SQL, func for SQL functions like SUM, strftime
from werkzeug.security import check_password_hash, generate_password_hash

# Load environment variables from .env file (if it exists)
load_dotenv()

# Configure application
app = Flask(__name__)

# Keep debug mode ON for development.
# In a production deployment, this would typically be set to False
# or overridden by the WSGI server (e.g., Gunicorn).
app.debug = True
app.config["DEBUG"] = True


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure Database for PostgreSQL using Flask-SQLAlchemy
# The DATABASE_URL will come from your .env file
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False # Suppresses a warning

print(f"DEBUG: SQLALCHEMY_DATABASE_URI is: {os.getenv('DATABASE_URL')}")
db = SQLAlchemy(app) # Initialize SQLAlchemy instance

# Ensure SECRET_KEY is loaded from .env for Flask's session security
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "a_very_secret_key_if_not_set_in_env") # Provide a fallback for development

# --- Flask-Mail Configuration ---
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() in ('true', '1', 't')
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)

# --- Token Serializer for Password Resets ---
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# JWT Setup
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "super-secret-jwt-key")
jwt = JWTManager(app)

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
    user_id = session["user_id"]

    selected_month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    selected_month_display = datetime.strptime(selected_month, '%Y-%m').strftime('%B %Y')

    available_months = []
    current_date = datetime.now()
    for i in range(12):
        year = current_date.year
        month = current_date.month - i
        if month <= 0:
            month += 12
            year -= 1
        month_start_date = datetime(year, month, 1)
        month_val = month_start_date.strftime('%Y-%m')
        month_label = month_start_date.strftime('%B %Y')
        available_months.append((month_val, month_label))
    available_months.reverse()

    # 1. Fetch Total Income for selected month
    income_items = execute_query_helper(db, """
        SELECT amount
        FROM income
        WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :selected_month
    """, {"user_id": user_id, "selected_month": selected_month})
    total_income = sum(float(item['amount']) for item in income_items) if income_items else 0.0

    # 2. Fetch Total Expenses for selected month
    expenses_items = execute_query_helper(db, """
        SELECT amount
        FROM expenses
        WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :selected_month
    """, {"user_id": user_id, "selected_month": selected_month})
    total_expenses = sum(float(item['amount']) for item in expenses_items) if expenses_items else 0.0

    # 3. Fetch Total Budget for selected month
    budget_items_monthly = execute_query_helper(db, """
        SELECT amount
        FROM budget
        WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :selected_month
    """, {"user_id": user_id, "selected_month": selected_month})
    total_budget = sum(float(item['amount']) for item in budget_items_monthly) if budget_items_monthly else 0.0

    # 4. Fetch Total Savings for selected month (UPDATED: now filtered by month)
    # Savings table doesn't have a date in your DDL, so this filtering might not make sense
    # If savings are associated with a date of deposit, you'll need a 'date' column in your savings table.
    # For now, I'm removing the month filter as per your DDL, if you add date column, you can put it back
    savings_items = execute_query_helper(db, """
        SELECT amount
        FROM savings
        WHERE user_id = :user_id
    """, {"user_id": user_id})
    total_savings = sum(float(item['amount']) for item in savings_items) if savings_items else 0.0

    # 5. Calculate Net Balance for selected month
    net_balance = total_income - total_expenses

    # 6. Budget vs. Actual Spending per Category (Filtered by selected_month for *expenses*)
    budget_vs_actual = {}

    relevant_expense_categories = execute_query_helper(db, """
        SELECT DISTINCT category
        FROM expenses
        WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :selected_month
    """, {"user_id": user_id, "selected_month": selected_month})

    if not relevant_expense_categories:
        budget_bar_labels = []
        budgeted_data = []
        spent_data = []
    else:
        for cat_entry in relevant_expense_categories:
            category = cat_entry['category']

            budgeted_amount_result = execute_query_helper(db, """
                SELECT amount FROM budget
                WHERE user_id = :user_id AND category = :category AND TO_CHAR(date, 'YYYY-MM') = :selected_month
            """, {"user_id": user_id, "category": category, "selected_month": selected_month}, fetch_one=True)
            budgeted_amount = float(budgeted_amount_result['amount']) if budgeted_amount_result and budgeted_amount_result['amount'] is not None else 0.0

            spent_amount_result = execute_query_helper(db, """
                SELECT SUM(amount) AS spent FROM expenses
                WHERE user_id = :user_id AND category = :category AND TO_CHAR(date, 'YYYY-MM') = :selected_month
            """, {"user_id": user_id, "category": category, "selected_month": selected_month}, fetch_one=True)
            spent_amount = float(spent_amount_result['spent']) if spent_amount_result and spent_amount_result['spent'] is not None else 0.0

            budget_vs_actual[category] = {
                "budgeted": budgeted_amount,
                "spent": spent_amount,
                "remaining": budgeted_amount - spent_amount
            }

        budget_bar_labels = list(budget_vs_actual.keys())
        budgeted_data = [d['budgeted'] for d in budget_vs_actual.values()]
        spent_data = [d['spent'] for d in budget_vs_actual.values()]

    # 7. Top Spending Categories (for Pie Chart) (Filtered by selected_month)
    top_expenses_by_category = execute_query_helper(db, """
        SELECT category, SUM(amount) AS total_spent
        FROM expenses
        WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :selected_month
        GROUP BY category
        ORDER BY total_spent DESC
        LIMIT 5
    """, {"user_id": user_id, "selected_month": selected_month})

    pie_chart_labels = [item['category'] for item in top_expenses_by_category]
    pie_chart_data = [float(item['total_spent']) for item in top_expenses_by_category] # Ensure float

    # 8. Daily Income vs. Expenses (for Line Chart) for the selected month
    daily_income_raw = execute_query_helper(db, """
        SELECT
            TO_CHAR(date, 'YYYY-MM-DD') AS day,
            SUM(amount) AS total_income
        FROM income
        WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :selected_month
        GROUP BY day
        ORDER BY day
    """, {"user_id": user_id, "selected_month": selected_month})

    daily_expenses_raw = execute_query_helper(db, """
        SELECT
            TO_CHAR(date, 'YYYY-MM-DD') AS day,
            SUM(amount) AS total_expenses
        FROM expenses
        WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :selected_month
        GROUP BY day
        ORDER BY day
    """, {"user_id": user_id, "selected_month": selected_month})

    monthly_income_total_result = execute_query_helper(db, """
        SELECT SUM(amount) AS total
        FROM income
        WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :selected_month
    """, {"user_id": user_id, "selected_month": selected_month}, fetch_one=True)
    monthly_income_total = float(monthly_income_total_result['total']) if monthly_income_total_result and monthly_income_total_result['total'] is not None else 0.0

    monthly_expenses_total_result = execute_query_helper(db, """
        SELECT SUM(amount) AS total
        FROM expenses
        WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :selected_month
    """, {"user_id": user_id, "selected_month": selected_month}, fetch_one=True)
    monthly_expenses_total = float(monthly_expenses_total_result['total']) if monthly_expenses_total_result and monthly_expenses_total_result['total'] is not None else 0.0

    daily_data = {}
    year, month = map(int, selected_month.split('-'))
    num_days_in_month = calendar.monthrange(year, month)[1]
    first_day_of_selected_month = datetime(year, month, 1)

    for i in range(num_days_in_month):
        current_day = first_day_of_selected_month + timedelta(days=i)
        formatted_date = current_day.strftime('%Y-%m-%d')
        daily_data[formatted_date] = {'income': 0.0, 'expenses': 0.0}

    for row in daily_income_raw:
        daily_data[row['day']]['income'] = float(row['total_income'])
    for row in daily_expenses_raw:
        daily_data[row['day']]['expenses'] = float(row['total_expenses'])

    sorted_days = sorted(daily_data.keys())
    line_chart_labels = []
    line_chart_income_data = []
    line_chart_expenses_data = []

    for day in sorted_days:
        line_chart_labels.append(datetime.strptime(
            day, '%Y-%m-%d').strftime('%b %d'))
        line_chart_income_data.append(daily_data[day]['income'])
        line_chart_expenses_data.append(daily_data[day]['expenses'])

    return render_template("index.html",
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
                           selected_month=selected_month,
                           selected_month_display=selected_month_display,
                           available_months=available_months,
                           monthly_income_total=monthly_income_total,
                           monthly_expenses_total=monthly_expenses_total)


@app.route("/savings_dashboard")
@login_required
def savings_dashboard():
    """Display user's savings goals, net worth, and financial health score"""
    user_id = session["user_id"]

    # Pass the 'db' instance to the helper function
    financial_data = _get_all_financial_metrics(db, user_id)

    return render_template("savings_dashboard.html",
                            savings_goals=financial_data["savings_goals"],
                            net_worth=financial_data["total_assets"] - financial_data["total_liabilities"],
                            cash_flow=financial_data["cash_flow"],
                            financial_health_score=financial_data["financial_health_score"],
                            score_details=financial_data["score_details"],
                            all_total_income=financial_data["all_total_income"],
                            all_total_expenses=financial_data["all_total_expenses"],
                            total_assets=financial_data["total_assets"]
                            )

@app.route("/api/financial_alerts_data")
@login_required
def api_financial_alerts_data():
    """API endpoint to provide financial alerts."""
    user_id = session["user_id"]
    # Pass the 'db' instance to the helper function
    alerts = _generate_financial_alerts_list(db, user_id)
    return jsonify(alerts)


@app.route("/api/delete_alert", methods=["POST"])
@login_required
def api_delete_alert():
    """API endpoint to permanently dismiss/delete a specific alert for the user."""
    user_id = session["user_id"]
    alert_hash = request.json.get("alert_hash")

    if not alert_hash:
        return jsonify({"success": False, "message": "Alert hash is required."}), 400

    try:
        db.session.execute(text(
            "INSERT INTO read_user_alerts (user_id, alert_hash) VALUES (:user_id, :alert_hash) ON CONFLICT (user_id, alert_hash) DO NOTHING"
        ), {"user_id": user_id, "alert_hash": alert_hash})
        db.session.commit() # Commit the transaction
        return jsonify({"success": True, "message": "Alert dismissed permanently."}), 200
    except Exception as e:
        db.session.rollback() # Rollback on error
        print(f"Error dismissing alert: {e}")
        return jsonify({"success": False, "message": "Failed to dismiss alert."}), 500

@app.route("/api/reset_alerts", methods=["POST"])
@login_required
def api_reset_alerts():
    """API endpoint to clear all dismissed alerts for the user."""
    user_id = session["user_id"]
    try:
        db.session.execute(text("DELETE FROM read_user_alerts WHERE user_id = :user_id"), {"user_id": user_id})
        db.session.commit() # Commit the transaction
        return jsonify({"success": True, "message": "All alerts have been reset."}), 200
    except Exception as e:
        db.session.rollback() # Rollback on error
        print(f"Error resetting alerts: {e}")
        return jsonify({"success": False, "message": "Failed to reset alerts."}), 500


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    """
    Handles forgotten password requests.
    If GET: Displays the email input form.
    If POST: Processes the email, generates a token, and sends a reset link.
    """
    if request.method == "POST":
        email = request.form.get("email")
        if not email:
            flash("Please enter your email address.", "danger")
            return redirect(url_for('forgot_password'))

        # Use your execute_query_helper to find the user by email
        user = execute_query_helper(db, "SELECT id, email FROM users WHERE email = :email", {"email": email}, fetch_one=True)

        if user:
            # Generate a token that expires after some time (e.g., 1 hour)
            token = s.dumps(user['email'], salt='password-reset-salt') # Use a distinct salt

            # Construct the reset link
            # For local development, this will be http://127.0.0.1:5000/reset_password/<token>
            reset_url = url_for('reset_password', token=token, _external=True)

            # Send the email
            try:
                msg = Message("Password Reset Request for Cash Compass",
                              sender=app.config['MAIL_DEFAULT_SENDER'],
                              recipients=[user['email']])
                msg.body = f"""
Dear {user['email']},

You have requested to reset your password for your Cash Compass account.

Please click on the following link to reset your password:
{reset_url}

This link is valid for 1 hour. If you did not request a password reset, please ignore this email.

Thank you,
The Cash Compass Team
                """
                mail.send(msg)
                flash("A password reset link has been sent to your email address.", "info")
            except Exception as e:
                flash(f"Failed to send email. Please check server configuration or try again later. Error: {e}", "danger")
                print(f"MAIL SEND ERROR: {e}")
        else:
            flash("If an account with that email exists, a password reset link has been sent.", "info")
            # We intentionally give a generic message for security reasons
            # to prevent enumeration of existing email addresses.

        return redirect(url_for('login')) # Redirect back to login page

    return render_template("forgot_password.html")

@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """
    Handles the password reset process after clicking the link.
    If GET: Verifies the token and displays the new password input form.
    If POST: Processes the new password and updates it in the database.
    """
    try:
        # Verify the token. max_age is in seconds (e.g., 3600 for 1 hour)
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except SignatureExpired:
        flash("The password reset link has expired. Please request a new one.", "danger")
        return redirect(url_for('forgot_password'))
    except BadTimeSignature:
        flash("The password reset link is invalid. Please request a new one.", "danger")
        return redirect(url_for('forgot_password'))
    except Exception as e:
        flash(f"An error occurred with the reset link. Please try again. Error: {e}", "danger")
        return redirect(url_for('forgot_password'))

    # Use your execute_query_helper to get user details
    user = execute_query_helper(db, "SELECT id, username FROM users WHERE email = :email", {"email": email}, fetch_one=True)
    if not user:
        flash("Account not found for this reset link.", "danger")
        return redirect(url_for('forgot_password'))

    if request.method == "POST":
        new_password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")

        if not new_password or not confirmation:
            return apology("Must provide and confirm new password", 400)
        if new_password != confirmation:
            return apology("New passwords do not match", 400)
        if len(new_password) < 6:
            return apology("New password must be at least 6 characters long", 400)

        new_password_hash = generate_password_hash(new_password)

        try:
            db.session.execute(text("""
                UPDATE users
                SET password_hash = :new_password_hash
                WHERE id = :user_id
            """), {"new_password_hash": new_password_hash, "user_id": user['id']})
            db.session.commit()
            flash("Your password has been reset successfully!", "success")
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to reset password due to a database error. Error: {e}", "danger")
            return redirect(url_for('reset_password', token=token)) # Stay on the reset page

    # For GET request, render the reset password form
    return render_template("reset_password.html", token=token, username=user['username'])


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 403)
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        rows = execute_query_helper(db,
            "SELECT id, username, password_hash FROM users WHERE username = :username",
            {"username": request.form.get("username")}
        )

        if len(rows) != 1 or not check_password_hash(
            rows[0]["password_hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        session["user_id"] = rows[0]["id"]
        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        email = request.form.get("email") # NEW: Get email from the form

        if not username:
            return apology("must provide username", 400)
        if not password:
            return apology("must provide password", 400)
        if not confirmation:
            return apology("must confirm password", 400)
        if password != confirmation:
            return apology("passwords do not match", 400)
        if not email: # NEW: Validate email presence
            return apology("must provide email", 400)

        hash_pass = generate_password_hash(password)

        try:
            # MODIFIED: Include email in the INSERT statement
            db.session.execute(text(
                "INSERT INTO users (username, password_hash, email) VALUES (:username, :password_hash, :email)"
            ), {"username": username, "password_hash": hash_pass, "email": email})
            db.session.commit() # Commit the transaction
        except Exception as e: # Catch a broader exception for database errors
            db.session.rollback() # Rollback on error
            # In PostgreSQL, UNIQUE constraint violation raises IntegrityError
            if "duplicate key value violates unique constraint" in str(e):
                # MODIFIED: Inform user about username OR email existing
                return apology("username or email already exists", 400)
            print(f"Error during registration: {e}")
            return apology("Registration failed due to a database error", 500)

        flash("Successfully registered! Please log in.")
        return redirect("/login")
    else:
        return render_template("register.html")


@app.route("/budget", methods=["GET", "POST"])
@login_required
def budget():
    """Manage budget"""
    user_id = session["user_id"]

    if request.method == "POST":
        category = request.form.get("category")
        amount = request.form.get("amount")
        budget_month_str = request.form.get("month")

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

        try:
            budget_date = datetime.strptime(budget_month_str, '%Y-%m').replace(day=1)
        except ValueError:
            flash("Invalid month format provided.", "danger")
            return redirect("/budget")

        db.session.execute(text("""
            INSERT INTO budget (user_id, category, amount, date)
            VALUES (:user_id, :category, :amount, :date)
        """), {
            "user_id": user_id,
            "category": category,
            "amount": amount,
            "date": budget_date # SQLAlchemy will handle datetime objects for PostgreSQL
        })
        db.session.commit()

        flash("Budget item added successfully!", "success")
        return redirect("/budget")

    else:
        selected_month = request.args.get('month', datetime.now().strftime('%Y-%m'))
        selected_month_display = datetime.strptime(selected_month, '%Y-%m').strftime('%B %Y')
        current_month_iso = datetime.now().strftime('%Y-%m')

        available_months = []
        current_date_for_dropdown = datetime.now()
        for i in range(12):
            year = current_date_for_dropdown.year
            month = current_date_for_dropdown.month - i
            if month <= 0:
                month += 12
                year -= 1
            month_start_date = datetime(year, month, 1)
            month_val = month_start_date.strftime('%Y-%m')
            month_label = month_start_date.strftime('%B %Y')
            available_months.append((month_val, month_label))
        available_months.reverse()

        budget_items = execute_query_helper(db, """
            SELECT id, category, amount, date
            FROM budget
            WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :selected_month
            ORDER BY category
        """, {"user_id": user_id, "selected_month": selected_month})

        total_budget = sum(float(item['amount']) for item in budget_items) if budget_items else 0.0

        return render_template("budget.html",
                               budget_items=budget_items,
                               total_budget=total_budget,
                               selected_month=selected_month,
                               selected_month_display=selected_month_display,
                               available_months=available_months,
                               current_month_iso=current_month_iso)

@app.route("/budget/edit/<int:item_id>", methods=["POST"])
@login_required
def edit_budget(item_id):
    """Edit a budget item"""
    user_id = session["user_id"]

    category = request.form.get("category")
    amount = request.form.get("amount")
    date_str = request.form.get("date")

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

    try:
        budget_date = datetime.strptime(date_str, '%Y-%m-%d').replace(day=1)
    except ValueError:
        flash("Invalid date format provided.", "danger")
        return redirect("/budget")

    db.session.execute(text("""
        UPDATE budget
        SET category = :category, amount = :amount, date = :date
        WHERE id = :id AND user_id = :user_id
    """), {
        "category": category,
        "amount": amount,
        "date": budget_date,
        "id": item_id,
        "user_id": user_id
    })
    db.session.commit()

    flash("Budget item updated successfully!", "success")
    return redirect("/budget")


@app.route("/budget/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_budget(item_id):
    """Delete a budget item"""
    user_id = session["user_id"]

    db.session.execute(text("""
        DELETE FROM budget
        WHERE id = :id AND user_id = :user_id
    """), {"id": item_id, "user_id": user_id})
    db.session.commit()

    flash("Budget item deleted successfully!", "success")
    return redirect("/budget")

@app.route("/expenses", methods=["GET", "POST"])
@login_required
def expenses():
    """Manage expenses"""
    user_id = session["user_id"]

    current_year = datetime.now().year
    current_month = datetime.now().month

    selected_month_str = request.args.get("month")
    if selected_month_str:
        try:
            selected_month_year = datetime.strptime(selected_month_str, "%Y-%m")
            selected_year = selected_month_year.year
            selected_month_num = selected_month_year.month
        except ValueError:
            selected_year = current_year
            selected_month_num = current_month
            selected_month_str = f"{selected_year}-{selected_month_num:02d}"
    else:
        selected_year = current_year
        selected_month_num = current_month
        selected_month_str = f"{selected_year}-{selected_month_num:02d}"

    selected_month_display = calendar.month_name[selected_month_num] + " " + str(selected_year)

    available_months = []
    for i in range(12):
        month_date = datetime(current_year, current_month, 1) - timedelta(days=30 * i)
        available_months.append((month_date.strftime("%Y-%m"), month_date.strftime("%B %Y")))
    available_months.reverse()
    available_months.append((datetime.now().strftime(
        "%Y-%m"), datetime.now().strftime("%B %Y") + " (Current)"))

    if request.method == "POST":
        category = request.form.get("category")
        amount = request.form.get("amount")
        date_str = request.form.get("date")

        if not category or not amount or not date_str:
            flash("Missing required expense information: Category, Amount, or Date.", "danger")
            return redirect("/expenses")

        try:
            amount = float(amount)
            if amount <= 0:
                flash("Amount must be a positive number.", "danger")
                return redirect("/expenses")
            expense_date = datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            flash("Invalid amount or date format.", "danger")
            return redirect("/expenses")

        db.session.execute(text("""
            INSERT INTO expenses (user_id, category, amount, date)
            VALUES (:user_id, :category, :amount, :date)
        """), {
            "user_id": user_id,
            "category": category,
            "amount": amount,
            "date": expense_date # SQLAlchemy will handle datetime objects for PostgreSQL
        })
        db.session.commit()

        flash("Expense added successfully!", "success")
        return redirect(url_for("expenses", month=selected_month_str))

    else:
        budget_categories = execute_query_helper(db, """
            SELECT category
            FROM budget
            WHERE user_id = :user_id
            GROUP BY category
            ORDER BY category
        """, {"user_id": user_id})
        categories = [row["category"] for row in budget_categories]

        expenses_items = execute_query_helper(db, """
            SELECT id, category, amount, date
            FROM expenses
            WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :selected_month
            ORDER BY date DESC, category
        """, {"user_id": user_id, "selected_month": selected_month_str})

        total_expenses = sum(float(item['amount']) for item in expenses_items)

        return render_template("expenses.html",
                               categories=categories,
                               expenses_items=expenses_items,
                               total_expenses=total_expenses,
                               available_months=available_months,
                               selected_month=selected_month_str,
                               selected_month_display=selected_month_display
                               )


@app.route("/expenses/edit/<int:item_id>", methods=["POST"])
@login_required
def edit_expense(item_id):
    """Edit an expense item"""
    user_id = session["user_id"]

    category = request.form.get("category")
    amount = request.form.get("amount")
    date_str = request.form.get("date")

    if not category:
        flash("Category cannot be empty", "danger")
        return redirect("/expenses")
    try:
        amount = float(amount)
        if amount <= 0:
            flash("Amount must be a positive number.", "danger")
            return redirect("/expenses")
        expense_date = datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        flash("Invalid amount or date format.", "danger")
        return redirect("/expenses")

    db.session.execute(text("""
        UPDATE expenses
        SET category = :category, amount = :amount, date = :date
        WHERE id = :id AND user_id = :user_id
    """), {
        "category": category,
        "amount": amount,
        "date": expense_date,
        "id": item_id,
        "user_id": user_id
    })
    db.session.commit()

    flash("Expense item updated successfully!", "success")
    selected_month_str = request.args.get("month")
    return redirect(url_for("expenses", month=selected_month_str if selected_month_str else datetime.now().strftime("%Y-%m")))


@app.route("/expenses/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_expense(item_id):
    """Delete an expense item"""
    user_id = session["user_id"]

    db.session.execute(text("""
        DELETE FROM expenses
        WHERE id = :id AND user_id = :user_id
    """), {"id": item_id, "user_id": user_id})
    db.session.commit()

    flash("Expense item deleted successfully!", "success")
    selected_month_str = request.args.get("month")
    return redirect(url_for("expenses", month=selected_month_str if selected_month_str else datetime.now().strftime("%Y-%m")))


@app.route("/income", methods=["GET", "POST"])
@login_required
def income():
    """Manage income"""
    user_id = session["user_id"]

    if request.method == "POST":
        source = request.form.get("source")
        amount = request.form.get("amount")
        income_date_str = request.form.get("date")

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

        try:
            income_date = datetime.strptime(income_date_str, '%Y-%m-%d')
        except ValueError:
            flash("Invalid date format provided.", "danger")
            return redirect("/income")

        db.session.execute(text("""
            INSERT INTO income (user_id, source, amount, date)
            VALUES (:user_id, :source, :amount, :date)
        """), {
            "user_id": user_id,
            "source": source,
            "amount": amount,
            "date": income_date
        })
        db.session.commit()

        flash("Income added successfully!", "success")
        return redirect("/income")

    else:
        selected_month = request.args.get('month', datetime.now().strftime('%Y-%m'))
        selected_month_display = datetime.strptime(selected_month, '%Y-%m').strftime('%B %Y')
        current_date_iso = datetime.now().strftime('%Y-%m-%d')

        available_months = []
        current_date_for_dropdown = datetime.now()
        for i in range(12):
            year = current_date_for_dropdown.year
            month = current_date_for_dropdown.month - i
            if month <= 0:
                month += 12
                year -= 1
            month_start_date = datetime(year, month, 1)
            month_val = month_start_date.strftime('%Y-%m')
            month_label = month_start_date.strftime('%B %Y')
            available_months.append((month_val, month_label))
        available_months.reverse()

        income_items = execute_query_helper(db, """
            SELECT id, source, amount, date
            FROM income
            WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :selected_month
            ORDER BY date DESC, source
        """, {"user_id": user_id, "selected_month": selected_month})

        total_income = sum(float(item['amount']) for item in income_items) if income_items else 0.0

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
    user_id = session["user_id"]

    source = request.form.get("source")
    amount = request.form.get("amount")
    date_str = request.form.get("date")

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

    try:
        income_date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        flash("Invalid date format provided.", "danger")
        return redirect("/income")

    db.session.execute(text("""
        UPDATE income
        SET source = :source, amount = :amount, date = :date
        WHERE id = :id AND user_id = :user_id
    """), {
        "source": source,
        "amount": amount,
        "date": income_date,
        "id": item_id,
        "user_id": user_id
    })
    db.session.commit()

    flash("Income item updated successfully!", "success")
    return redirect("/income")


@app.route("/income/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_income(item_id):
    """Delete an income item"""
    user_id = session["user_id"]

    db.session.execute(text("""
        DELETE FROM income
        WHERE id = :id AND user_id = :user_id
    """), {"id": item_id, "user_id": user_id})
    db.session.commit()

    flash("Income item deleted successfully!", "success")
    return redirect("/income")


@app.route("/savings", methods=["GET", "POST"])
@login_required
def savings():
    """Manage savings"""
    user_id = session["user_id"]

    if request.method == "POST":
        goal = request.form.get("goal")
        amount = request.form.get("amount")
        target_amount = request.form.get("target_amount")

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
        except (ValueError, TypeError):
            flash("Invalid target amount format", "danger")
            return redirect("/savings")

        db.session.execute(text("""
            INSERT INTO savings (user_id, goal, amount, target_amount)
            VALUES (:user_id, :goal, :amount, :target_amount)
        """), {
            "user_id": user_id,
            "goal": goal,
            "amount": amount,
            "target_amount": target_amount
        })
        db.session.commit()

        flash("Savings goal added successfully!", "success")
        return redirect("/savings")

    else:
        savings_items = execute_query_helper(db, """
            SELECT id, goal, amount, target_amount
            FROM savings
            WHERE user_id = :user_id
            ORDER BY goal
        """, {"user_id": user_id})

        total_current_savings = sum(float(item['amount']) for item in savings_items) if savings_items else 0.0

        return render_template("savings.html",
                               savings_items=savings_items,
                               total_current_savings=total_current_savings)


@app.route("/savings/edit/<int:item_id>", methods=["POST"])
@login_required
def edit_savings(item_id):
    """Edit a savings item"""
    user_id = session["user_id"]

    goal = request.form.get("goal")
    amount = request.form.get("amount")
    target_amount = request.form.get("target_amount")

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
    except (ValueError, TypeError):
        flash("Invalid target amount format", "danger")
        return redirect("/savings")

    db.session.execute(text("""
        UPDATE savings
        SET goal = :goal, amount = :amount, target_amount = :target_amount
        WHERE id = :id AND user_id = :user_id
    """), {
        "goal": goal,
        "amount": amount,
        "target_amount": target_amount,
        "id": item_id,
        "user_id": user_id
    })
    db.session.commit()

    flash("Savings item updated successfully!", "success")
    return redirect("/savings")


@app.route("/savings/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_savings(item_id):
    """Delete a savings item"""
    user_id = session["user_id"]

    db.session.execute(text("""
        DELETE FROM savings
        WHERE id = :id AND user_id = :user_id
    """), {"id": item_id, "user_id": user_id})
    db.session.commit()

    flash("Savings item deleted successfully!", "success")
    return redirect("/savings")


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """User profile management"""
    user_id = session["user_id"]

    user_data = execute_query_helper(db, """
        SELECT username, email, created_at
        FROM users
        WHERE id = :user_id
    """, {"user_id": user_id}, fetch_one=True) # Use fetch_one=True here

    if not user_data:
        flash("User profile not found. Please log in again.", "danger")
        return redirect("/login")

    user = user_data
    return render_template("profile.html", user=user)


@app.route("/debt", methods=["GET", "POST"])
@login_required
def debt():
    """Manage debt records"""
    user_id = session["user_id"]

    if request.method == "POST":
        debt_name = request.form.get("debt_name")
        debt_type = request.form.get("debt_type")
        current_balance = request.form.get("current_balance")
        due_date_str = request.form.get("due_date")

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

        due_date = due_date_str if due_date_str else None # Store as string or None

        db.session.execute(text("""
            INSERT INTO debt (user_id, debt_name, debt_type, current_balance, due_date)
            VALUES (:user_id, :debt_name, :debt_type, :current_balance, :due_date)
        """), {
            "user_id": user_id,
            "debt_name": debt_name,
            "debt_type": debt_type,
            "current_balance": current_balance,
            "due_date": due_date
        })
        db.session.commit()

        flash("Debt item added successfully!", "success")
        return redirect("/debt")

    else:
        debt_items = execute_query_helper(db, """
            SELECT id, debt_name, debt_type, original_amount, current_balance,
                   interest_rate, minimum_payment, due_date, start_date, end_date,
                   lender, notes
            FROM debt
            WHERE user_id = :user_id
            ORDER BY due_date ASC, debt_name ASC
        """, {"user_id": user_id})

        total_liabilities = sum(float(item['current_balance']) for item in debt_items) if debt_items else 0.0

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

    debt_name = request.form.get("debt_name")
    debt_type = request.form.get("debt_type")
    current_balance = request.form.get("current_balance")
    due_date_str = request.form.get("due_date")

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

    db.session.execute(text("""
        UPDATE debt
        SET debt_name = :debt_name, debt_type = :debt_type, current_balance = :current_balance, due_date = :due_date
        WHERE id = :id AND user_id = :user_id
    """), {
        "debt_name": debt_name,
        "debt_type": debt_type,
        "current_balance": current_balance,
        "due_date": due_date,
        "id": item_id,
        "user_id": user_id
    })
    db.session.commit()

    flash("Debt item updated successfully!", "success")
    return redirect("/debt")


@app.route("/debt/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_debt(item_id):
    """Delete a debt item"""
    user_id = session["user_id"]

    db.session.execute(text("""
        DELETE FROM debt
        WHERE id = :id AND user_id = :user_id
    """), {"id": item_id, "user_id": user_id})
    db.session.commit()

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

        user_row = execute_query_helper(db, "SELECT password_hash FROM users WHERE id = :user_id", {"user_id": user_id}, fetch_one=True)
        if not user_row:
            flash("User not found.", "danger")
            return redirect("/login")

        if not current_password or not check_password_hash(user_row["password_hash"], current_password):
            return apology("Invalid current password", 403)

        if not new_password or not confirmation:
            return apology("Must provide and confirm new password", 400)
        if new_password != confirmation:
            return apology("New passwords do not match", 400)
        if len(new_password) < 6:
            return apology("New password must be at least 6 characters long", 400)

        new_password_hash = generate_password_hash(new_password)

        db.session.execute(text("""
            UPDATE users
            SET password_hash = :new_password_hash
            WHERE id = :user_id
        """), {"new_password_hash": new_password_hash, "user_id": user_id})
        db.session.commit()

        flash("Password updated successfully!", "success")
        return redirect("/profile")

    else:
        user_data = execute_query_helper(db, "SELECT username, email FROM users WHERE id = :user_id", {"user_id": user_id}, fetch_one=True)

        if not user_data:
            flash("User data not found for settings. Please log in again.", "danger")
            return redirect("/login")

        user = user_data
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

        if not new_username:
            return apology("Username cannot be empty", 400)
        if not new_email:
            return apology("Email cannot be empty", 400)

        existing_user = execute_query_helper(db,
            "SELECT id FROM users WHERE username = :new_username AND id != :user_id",
            {"new_username": new_username, "user_id": user_id}, fetch_one=True
        )
        if existing_user:
            return apology("Username already taken", 400)

        db.session.execute(text("""
            UPDATE users
            SET username = :username, email = :email
            WHERE id = :user_id
        """), {"username": new_username, "email": new_email, "user_id": user_id})
        db.session.commit()

        flash("Profile updated successfully!", "success")
        return redirect("/profile")

    else:
        user_data = execute_query_helper(db, "SELECT username, email FROM users WHERE id = :user_id", {"user_id": user_id}, fetch_one=True)
        if not user_data:
            flash("User data not found for profile editing. Please log in again.", "danger")
            return redirect("/login")
        user = user_data
        return render_template("edit_profile.html", user=user)


@app.route("/profile/delete_account", methods=["GET", "POST"])
@login_required
def delete_account():
    """Allow user to delete their account after password confirmation."""
    user_id = session["user_id"]

    if request.method == "POST":
        password = request.form.get("password")

        user_row = execute_query_helper(db, "SELECT password_hash FROM users WHERE id = :user_id", {"user_id": user_id}, fetch_one=True)
        if not user_row:
            flash("User not found.", "danger")
            return redirect("/login")

        if not password or not check_password_hash(user_row["password_hash"], password):
            return apology("Invalid password", 403)

        try:
            # Delete in reverse order of foreign key dependencies
            db.session.execute(text("DELETE FROM budget WHERE user_id = :user_id"), {"user_id": user_id})
            db.session.execute(text("DELETE FROM savings WHERE user_id = :user_id"), {"user_id": user_id})
            db.session.execute(text("DELETE FROM expenses WHERE user_id = :user_id"), {"user_id": user_id})
            db.session.execute(text("DELETE FROM income WHERE user_id = :user_id"), {"user_id": user_id})
            db.session.execute(text("DELETE FROM debt WHERE user_id = :user_id"), {"user_id": user_id})
            db.session.execute(text("DELETE FROM read_user_alerts WHERE user_id = :user_id"), {"user_id": user_id})
            db.session.execute(text("DELETE FROM users WHERE id = :user_id"), {"user_id": user_id})
            db.session.commit()

            flash("Your account has been successfully deleted.", "info")
            session.pop('user_id', None)
            return redirect("/login")
        except Exception as e:
            db.session.rollback()
            print(f"Database error during account deletion: {e}")
            flash("An error occurred during account deletion. Please try again.", "danger")
            return redirect("/profile/delete_account")

    else:
        return render_template("delete_account.html")


@app.route("/financial_advisor", methods=["GET", "POST"])
@login_required
def financial_advisor():
    """AI Financial Advisor page."""
    user_id = session["user_id"]

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    financial_advice_html = None

    if request.method == "POST":
        # 1. Fetch financial data from your database using your helper
        # Pass the 'db' instance to the helper function
        financial_data = _get_all_financial_metrics(db, user_id)

        # 2. Build the prompt for the AI
        prompt = build_ai_prompt(financial_data)

        # 3. Make the Gemini API call (using gemini-2.0-flash)
        if not GEMINI_API_KEY:
            flash("AI Financial Advisor not configured. Please update your Key in your .env file.", "warning")
            return render_template("financial_advisor.html", financial_advice=None)

        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048,
            }
        }

        try:
            response = requests.post(api_url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
            response.raise_for_status()
            result = response.json()

            if result.get('candidates') and result['candidates'][0].get('content') and result['candidates'][0]['content'].get('parts'):
                ai_text_response = result['candidates'][0]['content']['parts'][0]['text']
                financial_advice_html = markdown.markdown(ai_text_response)
                flash("Financial advice generated successfully!", "success")
            else:
                flash("AI did not generate a valid response. Please try again.", "warning")
                financial_advice_html = None
        except requests.exceptions.RequestException as e:
            flash("Danger, failed to get AI advice. Make sure to update your actual gemini API key in your .env file.", "danger")
            financial_advice_html = None
        except Exception as e:
            flash(f"An unexpected error occurred: {e}", "danger")
            financial_advice_html = None

    return render_template("financial_advisor.html", financial_advice=financial_advice_html)


def build_ai_prompt(financial_data):
    """
    Helper function to construct the AI prompt based on user's financial data.
    (This function does not need database access itself, but consumes data from it)
    """
    format_currency = lambda val: f"${val:.2f}" if val is not None else 'N/A'
    format_number = lambda val: f"{val:.1f}" if val is not None else 'N/A'
    get_categories = lambda categories: ', '.join(categories) if categories else 'None'

    data = financial_data

    total_income_all_time = data.get('all_total_income', 0)
    total_expenses_all_time = data.get('all_total_expenses', 0)
    net_worth = data.get('net_worth', 0)
    cash_flow = data.get('cash_flow', 0)
    total_savings = data.get('total_savings', 0)
    total_debt = data.get('total_liabilities', 0) # Changed from 'current_debt' to 'total_liabilities'
    average_monthly_expenses = data.get('average_monthly_expenses', 0)
    emergency_fund_target_3_months = data.get('emergency_fund_target_3_months', 0)
    emergency_fund_coverage = data.get('emergency_fund_coverage', 0)
    over_budget_categories = data.get('over_budget_categories', [])
    top_spending_categories_str = data.get('top_spending_categories_str', 'None')


    has_significant_financial_data = (
        (total_income_all_time > 0) or (total_expenses_all_time > 0) or
        (total_savings > 0) or (total_debt > 0) or
        (net_worth != 0) or (cash_flow != 0) or
        (average_monthly_expenses > 0) or
        (emergency_fund_target_3_months > 0) or
        (emergency_fund_coverage > 0) or
        (len(over_budget_categories) > 0) or
        (top_spending_categories_str not in ['N/A', 'None', ''])
    )

    intro_message = ""
    if not has_significant_financial_data:
        intro_message = """
            Based on the provided financial data, it appears that very little or no financial transactions (income, expenses, savings, or debt) have been recorded yet, or all recorded values are zero.
            Please provide foundational financial advice tailored for someone starting to track their finances. Focus on:
            - The importance of consistent recording (income, expenses, savings, debt).
            - Basic steps to begin building a financial picture.
            - General best practices for financial health in the early stages (e.g., creating a simple budget, starting an emergency fund, understanding debt).
            Do not attempt to provide detailed analysis of specific numbers, as the data is minimal.
        """
    else:
        intro_message = """
            As a professional financial advisor, analyze the following financial data and provide comprehensive, actionable advice.
            Identify key strengths and areas for improvement based on these specific figures.
            Ensure your advice directly references the provided numerical data where applicable.
        """

    prompt = f"""
        {intro_message}

        **Financial Summary:**
        • Total Income (All Time): {format_currency(total_income_all_time)}
        • Total Expenses (All Time): {format_currency(total_expenses_all_time)}
        • Current Net Worth: {format_currency(net_worth)}
        • Overall Cash Flow: {format_currency(cash_flow)}
        • Total Savings: {format_currency(total_savings)}
        • Total Debt: {format_currency(total_debt)}
        • Average Monthly Expenses: {format_currency(average_monthly_expenses)}

        **Detailed Analysis:**
        • Emergency Fund Target (3 months): {format_currency(emergency_fund_target_3_months)}
        • Emergency Fund Coverage: {format_number(emergency_fund_coverage)} months
        • Over-Budget Categories: {get_categories(over_budget_categories)}
        • Top Spending Categories: {top_spending_categories_str}

        Please provide detailed advice covering:
        1. **Financial Health Assessment** - Overall financial position analysis
        2. **Net Worth & Cash Flow Optimization** - Strategies to improve financial position
        3. **Debt Management Strategy** - Prioritized debt payoff recommendations
        4. **Emergency Fund Planning** - Steps to build adequate emergency reserves
        5. **Budget Optimization** - Spending habit improvements and budget recommendations
        6. **Investment & Growth Opportunities** - Suggestions for wealth building
        7. **Risk Management** - Insurance and protection strategies
        8. **Action Plan** - Specific next steps with timelines

        Format your response with clear headings, bullet points, and actionable recommendations using Markdown. Be encouraging while being realistic about challenges and opportunities.
        Also ensure not to suggest any competitors or alternatives to our services.
    """
    return prompt

# --- API: Login (returns JWT) ---
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400
    user = execute_query_helper(db, "SELECT id, username, password_hash FROM users WHERE username = :username", {"username": username}, fetch_one=True)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"msg": "Invalid username or password"}), 401
    # FIX: Ensure identity is a string for Flask-JWT-Extended
    access_token = create_access_token(identity=str(user["id"]))
    return jsonify(access_token=access_token, username=user["username"])

# --- API: Register (JSON, no email/confirmation required) ---
@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400
    hash_pass = generate_password_hash(password)
    try:
        db.session.execute(text(
            "INSERT INTO users (username, password_hash) VALUES (:username, :password_hash)"
        ), {"username": username, "password_hash": hash_pass})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        if "duplicate key value violates unique constraint" in str(e):
            return jsonify({"msg": "username already exists"}), 400
        return jsonify({"msg": "Registration failed due to a database error"}), 500
    return jsonify({"msg": "Successfully registered! Please log in."}), 200

# --- API: Income CRUD ---
@app.route('/api/income', methods=['GET', 'POST'])
@jwt_required()
def api_income():
    user_id = get_jwt_identity()
    if request.method == 'GET':
        month = request.args.get('month')
        year = request.args.get('year')
        query = "SELECT id, user_id, source, amount, date FROM income WHERE user_id = :user_id"
        params = {"user_id": user_id}
        if month and year:
            query += " AND EXTRACT(MONTH FROM date) = :month AND EXTRACT(YEAR FROM date) = :year"
            params["month"] = int(month)
            params["year"] = int(year)
        elif year:
            query += " AND EXTRACT(YEAR FROM date) = :year"
            params["year"] = int(year)
        elif month:
            query += " AND EXTRACT(MONTH FROM date) = :month"
            params["month"] = int(month)
        result = db.session.execute(text(query), params)
        income_items = [dict(row) for row in result.mappings()]
        return jsonify({'income': income_items})
    elif request.method == 'POST':
        data = request.get_json()
        source = data.get('source')
        amount = data.get('amount')
        date = data.get('date')
        if not source or amount is None or not date:
            return jsonify({'msg': 'Missing required fields'}), 400
        db.session.execute(
            text("""
                INSERT INTO income (user_id, source, amount, date)
                VALUES (:user_id, :source, :amount, :date)
            """),
            {
                'user_id': user_id,
                'source': source,
                'amount': amount,
                'date': date
            }
        )
        db.session.commit()
        return jsonify({'msg': 'Income item added'}), 201

@app.route('/api/income/<int:item_id>', methods=['PUT', 'DELETE'])
@jwt_required()
def api_income_item(item_id):
    user_id = get_jwt_identity()
    if request.method == 'PUT':
        data = request.get_json()
        source = data.get('source')
        amount = data.get('amount')
        date = data.get('date')
        if not source or amount is None or not date:
            return jsonify({'msg': 'Missing required fields'}), 400
        db.session.execute(
            text("""
                UPDATE income
                SET source = :source, amount = :amount, date = :date
                WHERE id = :item_id AND user_id = :user_id
            """),
            {
                'source': source,
                'amount': amount,
                'date': date,
                'item_id': item_id,
                'user_id': user_id
            }
        )
        db.session.commit()
        return jsonify({'msg': 'Income item updated'})
    elif request.method == 'DELETE':
        db.session.execute(
            text("""
                DELETE FROM income
                WHERE id = :item_id AND user_id = :user_id
            """),
            {
                'item_id': item_id,
                'user_id': user_id
            }
        )
        db.session.commit()
        return jsonify({'msg': 'Income item deleted'})

# --- API: Expenses CRUD ---
@app.route('/api/expenses', methods=['GET', 'POST'])
@jwt_required()
def api_expenses():
    user_id = get_jwt_identity()
    if request.method == 'GET':
        # Optional: filter by month/year
        month = request.args.get('month')
        year = request.args.get('year')
        query = "SELECT id, user_id, category, amount, date FROM expenses WHERE user_id = :user_id"
        params = {"user_id": user_id}
        if month and year:
            query += " AND EXTRACT(MONTH FROM date) = :month AND EXTRACT(YEAR FROM date) = :year"
            params["month"] = int(month)
            params["year"] = int(year)
        elif year:
            query += " AND EXTRACT(YEAR FROM date) = :year"
            params["year"] = int(year)
        elif month:
            query += " AND EXTRACT(MONTH FROM date) = :month"
            params["month"] = int(month)
        result = db.session.execute(text(query), params)
        expense_items = [dict(row) for row in result.mappings()]
        return jsonify({'expenses': expense_items})
    elif request.method == 'POST':
        data = request.get_json()
        category = data.get('category')
        amount = data.get('amount')
        date = data.get('date')
        if not category or amount is None or not date:
            return jsonify({'msg': 'Missing required fields'}), 400
        db.session.execute(
            text("""
                INSERT INTO expenses (user_id, category, amount, date)
                VALUES (:user_id, :category, :amount, :date)
            """),
            {
                'user_id': user_id,
                'category': category,
                'amount': amount,
                'date': date
            }
        )
        db.session.commit()
        return jsonify({'msg': 'Expense item added'}), 201

@app.route('/api/expenses/<int:item_id>', methods=['PUT', 'DELETE'])
@jwt_required()
def api_expense_item(item_id):
    user_id = get_jwt_identity()
    if request.method == 'PUT':
        data = request.get_json()
        category = data.get('category')
        amount = data.get('amount')
        date = data.get('date')
        if not category or amount is None or not date:
            return jsonify({'msg': 'Missing required fields'}), 400
        db.session.execute(
            text("""
                UPDATE expenses
                SET category = :category, amount = :amount, date = :date
                WHERE id = :item_id AND user_id = :user_id
            """),
            {
                'category': category,
                'amount': amount,
                'date': date,
                'item_id': item_id,
                'user_id': user_id
            }
        )
        db.session.commit()
        return jsonify({'msg': 'Expense item updated'})
    elif request.method == 'DELETE':
        db.session.execute(
            text("""
                DELETE FROM expenses
                WHERE id = :item_id AND user_id = :user_id
            """),
            {
                'item_id': item_id,
                'user_id': user_id
            }
        )
        db.session.commit()
        return jsonify({'msg': 'Expense item deleted'})

# --- API: Budgets CRUD ---
@app.route('/api/budgets', methods=['GET', 'POST'])
@jwt_required()
def api_budgets():
    user_id = get_jwt_identity()
    if request.method == 'GET':
        # Optional: filter by month/year
        month = request.args.get('month')
        year = request.args.get('year')
        query = "SELECT id, user_id, category, amount, date FROM budget WHERE user_id = :user_id"
        params = {"user_id": user_id}
        if month and year:
            query += " AND EXTRACT(MONTH FROM date) = :month AND EXTRACT(YEAR FROM date) = :year"
            params["month"] = int(month)
            params["year"] = int(year)
        elif year:
            query += " AND EXTRACT(YEAR FROM date) = :year"
            params["year"] = int(year)
        elif month:
            query += " AND EXTRACT(MONTH FROM date) = :month"
            params["month"] = int(month)
        result = db.session.execute(text(query), params)
        budget_items = [dict(row) for row in result.mappings()]
        return jsonify({'budgets': budget_items})
    elif request.method == 'POST':
        data = request.get_json()
        category = data.get('category')
        amount = data.get('amount')
        date = data.get('date')
        if not category or amount is None or not date:
            return jsonify({'msg': 'Missing required fields'}), 400
        db.session.execute(
            text("""
                INSERT INTO budget (user_id, category, amount, date)
                VALUES (:user_id, :category, :amount, :date)
            """),
            {
                'user_id': user_id,
                'category': category,
                'amount': amount,
                'date': date
            }
        )
        db.session.commit()
        return jsonify({'msg': 'Budget item added'}), 201

@app.route('/api/budgets/<int:item_id>', methods=['PUT', 'DELETE'])
@jwt_required()
def api_budget_item(item_id):
    user_id = get_jwt_identity()
    if request.method == 'PUT':
        data = request.get_json()
        category = data.get('category')
        amount = data.get('amount')
        date = data.get('date')
        if not category or amount is None or not date:
            return jsonify({'msg': 'Missing required fields'}), 400
        db.session.execute(
            text("""
                UPDATE budget
                SET category = :category, amount = :amount, date = :date
                WHERE id = :item_id AND user_id = :user_id
            """),
            {
                'category': category,
                'amount': amount,
                'date': date,
                'item_id': item_id,
                'user_id': user_id
            }
        )
        db.session.commit()
        return jsonify({'msg': 'Budget item updated'})
    elif request.method == 'DELETE':
        db.session.execute(
            text("""
                DELETE FROM budget
                WHERE id = :item_id AND user_id = :user_id
            """),
            {
                'item_id': item_id,
                'user_id': user_id
            }
        )
        db.session.commit()
        return jsonify({'msg': 'Budget item deleted'})

# --- API: Savings CRUD ---
@app.route('/api/savings', methods=['GET', 'POST'])
@jwt_required()
def api_savings():
    user_id = get_jwt_identity()
    if request.method == 'GET':
        result = db.session.execute(
            text("SELECT id, goal, amount, target_amount FROM savings WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        savings_items = [dict(row) for row in result.mappings()]
        return jsonify({'savings': savings_items})
    elif request.method == 'POST':
        data = request.get_json()
        goal = data.get('goal')
        amount = data.get('amount')
        target_amount = data.get('target_amount')
        if not goal or amount is None or target_amount is None:
            return jsonify({'msg': 'Missing required fields'}), 400
        db.session.execute(
            text("""
                INSERT INTO savings (user_id, goal, amount, target_amount)
                VALUES (:user_id, :goal, :amount, :target_amount)
            """),
            {
                'user_id': user_id,
                'goal': goal,
                'amount': amount,
                'target_amount': target_amount
            }
        )
        db.session.commit()
        return jsonify({'msg': 'Savings item added'}), 201

@app.route('/api/savings/<int:item_id>', methods=['PUT', 'DELETE'])
@jwt_required()
def api_savings_item(item_id):
    user_id = get_jwt_identity()
    if request.method == 'PUT':
        data = request.get_json()
        goal = data.get('goal')
        amount = data.get('amount')
        target_amount = data.get('target_amount')
        if not goal or amount is None or target_amount is None:
            return jsonify({'msg': 'Missing required fields'}), 400
        db.session.execute(
            text("""
                UPDATE savings
                SET goal = :goal, amount = :amount, target_amount = :target_amount
                WHERE id = :item_id AND user_id = :user_id
            """),
            {
                'goal': goal,
                'amount': amount,
                'target_amount': target_amount,
                'item_id': item_id,
                'user_id': user_id
            }
        )
        db.session.commit()
        return jsonify({'msg': 'Savings item updated'})
    elif request.method == 'DELETE':
        db.session.execute(
            text("""
                DELETE FROM savings
                WHERE id = :item_id AND user_id = :user_id
            """),
            {
                'item_id': item_id,
                'user_id': user_id
            }
        )
        db.session.commit()
        return jsonify({'msg': 'Savings item deleted'})

# --- API: Debt CRUD ---
@app.route('/api/debt', methods=['GET', 'POST'])
@jwt_required()
def api_debt():
    user_id = get_jwt_identity()
    if request.method == 'GET':
        result = db.session.execute(
            text("""
                SELECT id, debt_name, debt_type, current_balance, due_date
                FROM debt
                WHERE user_id = :user_id
                ORDER BY due_date ASC, debt_name ASC
            """),
            {"user_id": user_id}
        )
        debt_items = []
        for row in result.mappings():
            debt = dict(row)
            # Ensure due_date is always a string
            if 'due_date' in debt and debt['due_date'] is not None:
                if isinstance(debt['due_date'], (datetime, date)):
                    debt['due_date'] = debt['due_date'].isoformat()
                else:
                    debt['due_date'] = str(debt['due_date'])
            debt_items.append(debt)
        return jsonify({'debt': debt_items})
    elif request.method == 'POST':
        data = request.get_json()
        debt_name = data.get('debt_name')
        debt_type = data.get('debt_type')
        current_balance = data.get('current_balance')
        due_date = data.get('due_date')
        if not debt_name or not debt_type or current_balance is None:
            return jsonify({'msg': 'Missing required fields'}), 400
        db.session.execute(
            text("""
                INSERT INTO debt (user_id, debt_name, debt_type, current_balance, due_date)
                VALUES (:user_id, :debt_name, :debt_type, :current_balance, :due_date)
            """),
            {
                'user_id': user_id,
                'debt_name': debt_name,
                'debt_type': debt_type,
                'current_balance': current_balance,
                'due_date': due_date
            }
        )
        db.session.commit()
        return jsonify({'msg': 'Debt item added'}), 201

@app.route('/api/debt/<int:item_id>', methods=['PUT', 'DELETE'])
@jwt_required()
def api_debt_item(item_id):
    user_id = get_jwt_identity()
    if request.method == 'PUT':
        data = request.get_json()
        debt_name = data.get('debt_name')
        debt_type = data.get('debt_type')
        current_balance = data.get('current_balance')
        due_date = data.get('due_date')
        if not debt_name or not debt_type or current_balance is None:
            return jsonify({'msg': 'Missing required fields'}), 400
        db.session.execute(
            text("""
                UPDATE debt
                SET debt_name = :debt_name, debt_type = :debt_type, current_balance = :current_balance, due_date = :due_date
                WHERE id = :item_id AND user_id = :user_id
            """),
            {
                'debt_name': debt_name,
                'debt_type': debt_type,
                'current_balance': current_balance,
                'due_date': due_date,
                'item_id': item_id,
                'user_id': user_id
            }
        )
        db.session.commit()
        return jsonify({'msg': 'Debt item updated'})
    elif request.method == 'DELETE':
        db.session.execute(
            text("""
                DELETE FROM debt
                WHERE id = :item_id AND user_id = :user_id
            """),
            {
                'item_id': item_id,
                'user_id': user_id
            }
        )
        db.session.commit()
        return jsonify({'msg': 'Debt item deleted'})

# --- API: Profile ---
@app.route('/api/profile', methods=['GET', 'PUT'])
@jwt_required()
def api_profile():
    user_id = get_jwt_identity()
    if request.method == 'GET':
        # Fetch user profile info
        user = execute_query_helper(db, """
            SELECT id, username, email, created_at
            FROM users
            WHERE id = :user_id
        """, {"user_id": user_id}, fetch_one=True)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({'profile': user})
    elif request.method == 'PUT':
        data = request.get_json()
        # TODO: Update user profile info
        return jsonify({'msg': 'Profile updated'})

# --- API: Forgot Password ---
@app.route('/api/forgot_password', methods=['POST'])
def api_forgot_password():
    data = request.get_json()
    
    return jsonify({'msg': 'If the email exists, a reset link was sent.'})

# --- API: Reset Password ---
@app.route('/api/reset_password', methods=['POST'])
def api_reset_password():
    data = request.get_json()
    
    return jsonify({'msg': 'Password has been reset.'})

# --- API: AI Financial Advisor (JSON for mobile) ---
@app.route('/api/ai_advisor', methods=['POST'])
@jwt_required()
def api_ai_advisor():
    user_id = get_jwt_identity()
    # Use the same logic as /financial_advisor to get financial data
    financial_data = _get_all_financial_metrics(db, user_id)
    prompt = build_ai_prompt(financial_data)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        return jsonify({'error': 'AI Financial Advisor not configured. Please update your Key in your .env file.'}), 500
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 2048,
        }
    }
    try:
        import requests
        import markdown
        response = requests.post(api_url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()
        if result.get('candidates') and result['candidates'][0].get('content') and result['candidates'][0]['content'].get('parts'):
            ai_text_response = result['candidates'][0]['content']['parts'][0]['text']
            # Return as markdown/plain text for mobile
            return jsonify({'advice': ai_text_response})
        else:
            return jsonify({'error': 'AI did not generate a valid response.'}), 500
    except Exception as e:
        return jsonify({'error': f'Failed to get AI advice: {e}'}), 500



@app.route('/api/settings', methods=['GET', 'PUT'])
@jwt_required()
def api_settings():
    user_id = get_jwt_identity()
    if request.method == 'GET':
        result = db.session.execute(
            text("SELECT key, value FROM user_settings WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        settings = [dict(row) for row in result.mappings()]
        return jsonify(settings)
    elif request.method == 'PUT':
        data = request.get_json() or {}
        # data should be a dict of key: value pairs
        for key, value in data.items():
            db.session.execute(
                text("""
                    INSERT INTO user_settings (user_id, key, value)
                    VALUES (:user_id, :key, :value)
                    ON CONFLICT (user_id, key) DO UPDATE SET value = :value
                """),
                {"user_id": user_id, "key": key, "value": value}
            )
        db.session.commit()
        return jsonify({'msg': 'Settings updated'})

# --- API: Profile Update (PUT) ---
@app.route('/api/profile', methods=['PUT'])
@jwt_required()
def api_profile_update():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    new_username = data.get('username')
    new_email = data.get('email')
    if not new_username or not new_email:
        return jsonify({'msg': 'Username and email are required.'}), 400
    # Check for username conflict
    existing_user = execute_query_helper(db,
        "SELECT id FROM users WHERE username = :new_username AND id != :user_id",
        {"new_username": new_username, "user_id": user_id}, fetch_one=True)
    if existing_user:
        return jsonify({'msg': 'Username already taken.'}), 400
    db.session.execute(text("""
        UPDATE users SET username = :username, email = :email WHERE id = :user_id
    """), {"username": new_username, "email": new_email, "user_id": user_id})
    db.session.commit()
    return jsonify({'msg': 'Profile updated successfully.'})

# --- API: Change Password ---
@app.route('/api/change_password', methods=['POST'])
@jwt_required()
def api_change_password():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    if not current_password or not new_password:
        return jsonify({'msg': 'Current and new password are required.'}), 400
    user_row = execute_query_helper(db, "SELECT password_hash FROM users WHERE id = :user_id", {"user_id": user_id}, fetch_one=True)
    if not user_row or not check_password_hash(user_row["password_hash"], current_password):
        return jsonify({'msg': 'Invalid current password.'}), 403
    if len(new_password) < 6:
        return jsonify({'msg': 'New password must be at least 6 characters.'}), 400
    new_password_hash = generate_password_hash(new_password)
    db.session.execute(text("""
        UPDATE users SET password_hash = :new_password_hash WHERE id = :user_id
    """), {"new_password_hash": new_password_hash, "user_id": user_id})
    db.session.commit()
    return jsonify({'msg': 'Password updated successfully.'})

# --- API: Delete Account ---
@app.route('/api/delete_account', methods=['POST'])
@jwt_required()
def api_delete_account():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    password = data.get('password')
    user_row = execute_query_helper(db, "SELECT password_hash FROM users WHERE id = :user_id", {"user_id": user_id}, fetch_one=True)
    if not user_row or not check_password_hash(user_row["password_hash"], password):
        return jsonify({'msg': 'Invalid password.'}), 403
    try:
        db.session.execute(text("DELETE FROM budget WHERE user_id = :user_id"), {"user_id": user_id})
        db.session.execute(text("DELETE FROM savings WHERE user_id = :user_id"), {"user_id": user_id})
        db.session.execute(text("DELETE FROM expenses WHERE user_id = :user_id"), {"user_id": user_id})
        db.session.execute(text("DELETE FROM income WHERE user_id = :user_id"), {"user_id": user_id})
        db.session.execute(text("DELETE FROM debt WHERE user_id = :user_id"), {"user_id": user_id})
        db.session.execute(text("DELETE FROM read_user_alerts WHERE user_id = :user_id"), {"user_id": user_id})
        db.session.execute(text("DELETE FROM user_settings WHERE user_id = :user_id"), {"user_id": user_id})
        db.session.execute(text("DELETE FROM users WHERE id = :user_id"), {"user_id": user_id})
        db.session.commit()
        return jsonify({'msg': 'Account deleted successfully.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': f'Error deleting account: {e}'}), 500

@app.route('/api/dashboard', methods=['GET'])
@jwt_required()
def api_dashboard_full():
    user_id = get_jwt_identity()
    selected_month = request.args.get('month')
    if not selected_month:
        selected_month = datetime.now().strftime('%Y-%m')
    selected_month_display = datetime.strptime(selected_month, '%Y-%m').strftime('%B %Y')

    # --- Current Month Data (as before) ---
    income_items = execute_query_helper(db, """
        SELECT amount
        FROM income
        WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :selected_month
    """, {"user_id": user_id, "selected_month": selected_month})
    total_income = sum(float(item['amount']) for item in income_items) if income_items else 0.0

    expenses_items = execute_query_helper(db, """
        SELECT amount
        FROM expenses
        WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :selected_month
    """, {"user_id": user_id, "selected_month": selected_month})
    total_expenses = sum(float(item['amount']) for item in expenses_items) if expenses_items else 0.0

    budget_items_monthly = execute_query_helper(db, """
        SELECT amount
        FROM budget
        WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :selected_month
    """, {"user_id": user_id, "selected_month": selected_month})
    total_budget = sum(float(item['amount']) for item in budget_items_monthly) if budget_items_monthly else 0.0

    savings_items = execute_query_helper(db, """
        SELECT amount
        FROM savings
        WHERE user_id = :user_id
    """, {"user_id": user_id})
    total_savings = sum(float(item['amount']) for item in savings_items) if savings_items else 0.0

    net_balance = total_income - total_expenses

    # --- Top Income Sources (current month) ---
    top_income_sources = execute_query_helper(db, """
        SELECT source, SUM(amount) AS amount
        FROM income
        WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :selected_month
        GROUP BY source
        ORDER BY amount DESC
        LIMIT 3
    """, {"user_id": user_id, "selected_month": selected_month})
    top_income_sources = [{"source": row["source"], "amount": float(row["amount"])} for row in top_income_sources] if top_income_sources else []

    # --- Top Expense Categories (current month) ---
    top_expense_categories = execute_query_helper(db, """
        SELECT category, SUM(amount) AS amount
        FROM expenses
        WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :selected_month
        GROUP BY category
        ORDER BY amount DESC
        LIMIT 3
    """, {"user_id": user_id, "selected_month": selected_month})
    top_expense_categories = [{"category": row["category"], "amount": float(row["amount"])} for row in top_expense_categories] if top_expense_categories else []

    # --- Last Month Data ---
    last_month_dt = datetime.strptime(selected_month, '%Y-%m') - timedelta(days=1)
    last_month = last_month_dt.strftime('%Y-%m')
    last_month_income_items = execute_query_helper(db, """
        SELECT amount
        FROM income
        WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :last_month
    """, {"user_id": user_id, "last_month": last_month})
    last_month_income = sum(float(item['amount']) for item in last_month_income_items) if last_month_income_items else 0.0

    last_month_expenses_items = execute_query_helper(db, """
        SELECT amount
        FROM expenses
        WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :last_month
    """, {"user_id": user_id, "last_month": last_month})
    last_month_expenses = sum(float(item['amount']) for item in last_month_expenses_items) if last_month_expenses_items else 0.0

    last_month_savings_items = execute_query_helper(db, """
        SELECT amount
        FROM savings
        WHERE user_id = :user_id
    """, {"user_id": user_id})
    last_month_savings = sum(float(item['amount']) for item in last_month_savings_items) if last_month_savings_items else 0.0

    last_month_net_balance = last_month_income - last_month_expenses

    # --- Savings Goal (if available) ---
    savings_goal_row = execute_query_helper(db, """
        SELECT value FROM user_settings WHERE user_id = :user_id AND key = 'savings_goal'
    """, {"user_id": user_id}, fetch_one=True)
    savings_goal = float(savings_goal_row['value']) if savings_goal_row and savings_goal_row['value'] is not None else 0.0

    # 6. Budget vs. Actual Spending per Category (Filtered by selected_month for *expenses*)
    budget_vs_actual = {}

    relevant_expense_categories = execute_query_helper(db, """
        SELECT DISTINCT category
        FROM expenses
        WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :selected_month
    """, {"user_id": user_id, "selected_month": selected_month})

    if not relevant_expense_categories:
        budget_bar_labels = []
        budgeted_data = []
        spent_data = []
    else:
        for cat_entry in relevant_expense_categories:
            category = cat_entry['category']

            budgeted_amount_result = execute_query_helper(db, """
                SELECT amount FROM budget
                WHERE user_id = :user_id AND category = :category AND TO_CHAR(date, 'YYYY-MM') = :selected_month
            """, {"user_id": user_id, "category": category, "selected_month": selected_month}, fetch_one=True)
            budgeted_amount = float(budgeted_amount_result['amount']) if budgeted_amount_result and budgeted_amount_result['amount'] is not None else 0.0

            spent_amount_result = execute_query_helper(db, """
                SELECT SUM(amount) AS spent FROM expenses
                WHERE user_id = :user_id AND category = :category AND TO_CHAR(date, 'YYYY-MM') = :selected_month
            """, {"user_id": user_id, "category": category, "selected_month": selected_month}, fetch_one=True)
            spent_amount = float(spent_amount_result['spent']) if spent_amount_result and spent_amount_result['spent'] is not None else 0.0

            budget_vs_actual[category] = {
                "budgeted": budgeted_amount,
                "spent": spent_amount,
                "remaining": budgeted_amount - spent_amount
            }

        budget_bar_labels = list(budget_vs_actual.keys())
        budgeted_data = [d['budgeted'] for d in budget_vs_actual.values()]
        spent_data = [d['spent'] for d in budget_vs_actual.values()]

    # 7. Top Spending Categories (for Pie Chart) (Filtered by selected_month)
    top_expenses_by_category = execute_query_helper(db, """
        SELECT category, SUM(amount) AS total_spent
        FROM expenses
        WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :selected_month
        GROUP BY category
        ORDER BY total_spent DESC
        LIMIT 5
    """, {"user_id": user_id, "selected_month": selected_month})

    pie_chart_labels = [item['category'] for item in top_expenses_by_category]
    pie_chart_data = [float(item['total_spent']) for item in top_expenses_by_category] # Ensure float

    # 8. Daily Income vs. Expenses (for Line Chart) for the selected month
    daily_income_raw = execute_query_helper(db, """
        SELECT
            TO_CHAR(date, 'YYYY-MM-DD') AS day,
            SUM(amount) AS total_income
        FROM income
        WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :selected_month
        GROUP BY day
        ORDER BY day
    """, {"user_id": user_id, "selected_month": selected_month})

    daily_expenses_raw = execute_query_helper(db, """
        SELECT
            TO_CHAR(date, 'YYYY-MM-DD') AS day,
            SUM(amount) AS total_expenses
        FROM expenses
        WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :selected_month
        GROUP BY day
        ORDER BY day
    """, {"user_id": user_id, "selected_month": selected_month})

    monthly_income_total_result = execute_query_helper(db, """
        SELECT SUM(amount) AS total
        FROM income
        WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :selected_month
    """, {"user_id": user_id, "selected_month": selected_month}, fetch_one=True)
    monthly_income_total = float(monthly_income_total_result['total']) if monthly_income_total_result and monthly_income_total_result['total'] is not None else 0.0

    monthly_expenses_total_result = execute_query_helper(db, """
        SELECT SUM(amount) AS total
        FROM expenses
        WHERE user_id = :user_id AND TO_CHAR(date, 'YYYY-MM') = :selected_month
    """, {"user_id": user_id, "selected_month": selected_month}, fetch_one=True)
    monthly_expenses_total = float(monthly_expenses_total_result['total']) if monthly_expenses_total_result and monthly_expenses_total_result['total'] is not None else 0.0

    daily_data = {}
    year, month = map(int, selected_month.split('-'))
    num_days_in_month = calendar.monthrange(year, month)[1]
    first_day_of_selected_month = datetime(year, month, 1)

    for i in range(num_days_in_month):
        current_day = first_day_of_selected_month + timedelta(days=i)
        formatted_date = current_day.strftime('%Y-%m-%d')
        daily_data[formatted_date] = {'income': 0.0, 'expenses': 0.0}

    for row in daily_income_raw:
        daily_data[row['day']]['income'] = float(row['total_income'])
    for row in daily_expenses_raw:
        daily_data[row['day']]['expenses'] = float(row['total_expenses'])

    sorted_days = sorted(daily_data.keys())
    line_chart_labels = []
    line_chart_income_data = []
    line_chart_expenses_data = []

    for day in sorted_days:
        line_chart_labels.append(datetime.strptime(
            day, '%Y-%m-%d').strftime('%b %d'))
        line_chart_income_data.append(daily_data[day]['income'])
        line_chart_expenses_data.append(daily_data[day]['expenses'])

    # Generate available months (last 12 months, as yyyy-MM)
    available_months = []
    current_date = datetime.now()
    for i in range(12):
        year = current_date.year
        month = current_date.month - i
        if month <= 0:
            month += 12
            year -= 1
        month_start_date = datetime(year, month, 1)
        month_val = month_start_date.strftime('%Y-%m')
        available_months.append(month_val)
    available_months.reverse()

    return jsonify({
        'total_income': total_income,
        'total_expenses': total_expenses,
        'total_budget': total_budget,
        'total_savings': total_savings,
        'net_balance': net_balance,
        'top_income_sources': top_income_sources,
        'top_expense_categories': top_expense_categories,
        'last_month_income': last_month_income,
        'last_month_expenses': last_month_expenses,
        'last_month_savings': last_month_savings,
        'last_month_net_balance': last_month_net_balance,
        'savings_goal': savings_goal,
        'budget_vs_actual': budget_vs_actual,
        'budget_bar_labels': budget_bar_labels,
        'budgeted_data': budgeted_data,
        'spent_data': spent_data,
        'pie_chart_labels': pie_chart_labels,
        'pie_chart_data': pie_chart_data,
        'line_chart_labels': line_chart_labels,
        'line_chart_income_data': line_chart_income_data,
        'line_chart_expenses_data': line_chart_expenses_data,
        'selected_month': selected_month,
        'selected_month_display': selected_month_display,
        'monthly_income_total': monthly_income_total,
        'monthly_expenses_total': monthly_expenses_total,
        'available_months': available_months
    })

@app.route('/api/financial_health', methods=['GET'])
@jwt_required()
def api_financial_health():
    user_id = get_jwt_identity()
    financial_data = _get_all_financial_metrics(db, user_id)
    return jsonify({
        'savings_goals': financial_data["savings_goals"],
        'net_worth': financial_data["total_assets"] - financial_data["total_liabilities"],
        'cash_flow': financial_data["cash_flow"],
        'financial_health_score': financial_data["financial_health_score"],
        'score_details': financial_data["score_details"],
        'all_total_income': financial_data["all_total_income"],
        'all_total_expenses': financial_data["all_total_expenses"],
        'total_assets': financial_data["total_assets"],
        'total_liabilities': financial_data["total_liabilities"]
    })






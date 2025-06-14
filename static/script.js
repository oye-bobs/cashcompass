/*
 * Custom JavaScript for Sidebar Toggle functionality.
 * Toggles the 'active' class on the sidebar and 'shifted' class on the main content wrapper.
 * Also includes global alert generation logic.
 */
document.addEventListener('DOMContentLoaded', function() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const mainContentWrapper = document.getElementById('mainContentWrapper');
    const alertsModalBody = document.getElementById('alertsModalBody');
    const alertBadge = document.getElementById('alertBadge');

    // --- Sidebar Toggle Logic ---
    if (sidebarToggle && sidebar && mainContentWrapper) {
        sidebarToggle.addEventListener('click', function(event) {
            event.stopPropagation();
            sidebar.classList.toggle('active');
            mainContentWrapper.classList.toggle('shifted');
        });

        document.addEventListener('click', function(event) {
            if (sidebar.classList.contains('active')) {
                if (!sidebar.contains(event.target) && event.target !== sidebarToggle) {
                    sidebar.classList.remove('active');
                    mainContentWrapper.classList.remove('shifted');
                }
            }
        });
    } else {
        console.error('One or more elements for sidebar toggle not found. Ensure sidebarToggle, sidebar, and mainContentWrapper exist.');
    }

    // --- Auto-dismissing Flash Messages ---
    const alerts = document.querySelectorAll('.alert');

    alerts.forEach(alert => {
        if (alert.classList.contains('alert-dismissible')) {
            setTimeout(() => {
                const bootstrapAlert = bootstrap.Alert.getInstance(alert);
                if (bootstrapAlert) {
                    bootstrapAlert.dispose();
                } else {
                    alert.remove();
                }
            }, 5000);
        }
    });

    // --- Global Alerts Logic ---
    let activeAlerts = []; // This will hold the current active alerts

    /**
     * Generates and displays financial alerts based on provided data.
     * This function should be called from individual pages (e.g., dashboard.html)
     * after they fetch their specific data from the Flask backend.
     *
     * @param {Array} debtItems - Array of debt objects: [{ id, debt_name, current_balance, due_date }]
     * @param {Object} budgetVsActual - Object mapping categories to budget/spent/remaining data: { "Food": { budgeted, spent, remaining } }
     * @param {Array} savingsGoals - Array of savings goal objects: [{ id, goal, current_amount, target_amount }]
     * @param {number} cashFlowValue - The current cash flow value.
     */
    window.initializeAlerts = function(debtItems, budgetVsActual, savingsGoals, cashFlowValue) {
        activeAlerts = []; // Clear previous alerts
        if (alertsModalBody) {
            alertsModalBody.innerHTML = ''; // Clear modal content
        } else {
            console.warn('Alerts modal body not found, cannot display alerts.');
            return;
        }

        const today = new Date();
        today.setHours(0, 0, 0, 0); // Normalize to start of day

        // 1. Debt Due Date Approaching
        debtItems.forEach(debt => {
            if (debt.due_date) {
                const dueDate = new Date(debt.due_date + 'T00:00:00'); // Ensure UTC for comparison
                dueDate.setHours(0, 0, 0, 0);

                const timeDiff = dueDate.getTime() - today.getTime();
                const diffDays = Math.ceil(timeDiff / (1000 * 60 * 60 * 24));

                if (diffDays >= 0 && diffDays <= 7) { // Due in next 7 days or today
                    activeAlerts.push({
                        type: 'danger',
                        message: `<strong>Debt Due Soon:</strong> Your <strong>${debt.debt_name}</strong> of <strong>$${debt.current_balance.toFixed(2)}</strong> is due on <strong>${debt.due_date}</strong> (in ${diffDays} day(s)).`,
                        icon: 'fas fa-exclamation-circle'
                    });
                }
            }
        });

        // 2. Spent Above Budget
        for (const category in budgetVsActual) {
            const data = budgetVsActual[category];
            if (data.remaining < 0) {
                activeAlerts.push({
                    type: 'warning',
                    message: `<strong>Budget Alert:</strong> You are <strong>$${Math.abs(data.remaining).toFixed(2)}</strong> over budget for <strong>${category}</strong>.`,
                    icon: 'fas fa-wallet'
                });
            }
        }

        // 3. Savings Goal Reached
        savingsGoals.forEach(goal => {
            if (goal.current_amount >= goal.target_amount && goal.target_amount > 0) {
                activeAlerts.push({
                    type: 'success',
                    message: `<strong>Goal Achieved!</strong> You have reached your <strong>${goal.goal}</strong> goal of <strong>$${goal.target_amount.toFixed(2)}</strong>!`,
                    icon: 'fas fa-trophy'
                });
            }
        });

        // 4. Low Cash Flow / Negative Cash Flow
        if (cashFlowValue < 0) {
             activeAlerts.push({
                type: 'danger',
                message: `<strong>Negative Cash Flow:</strong> Your current cash flow is <strong>$${cashFlowValue.toFixed(2)}</strong>. Consider reviewing your income and expenses.`,
                icon: 'fas fa-chart-line'
            });
        } else if (cashFlowValue > 0 && cashFlowValue < 100) { // Small positive cash flow threshold
            activeAlerts.push({
                type: 'warning',
                message: `<strong>Low Cash Flow:</strong> Your current cash flow is <strong>$${cashFlowValue.toFixed(2)}</strong>. Look for ways to increase income or reduce expenses.`,
                icon: 'fas fa-chart-line'
            });
        }

        // 5. High Debt (New Creative Alert)
        // This requires `total_liabilities` to be passed from Flask (or calculated)
        const totalDebtValue = debtItems.reduce((sum, debt) => sum + debt.current_balance, 0);
        // Define a high debt threshold, e.g., if total debt is more than 50% of annual income or a fixed value
        // For simplicity, let's use a fixed high threshold (e.g., > $10,000 for a warning, > $20,000 for danger)
        const highDebtThresholdWarning = 10000; // Example
        const highDebtThresholdDanger = 20000; // Example

        if (totalDebtValue > highDebtThresholdDanger) {
             activeAlerts.push({
                type: 'danger',
                message: `<strong>High Debt Alert:</strong> Your total debt is <strong>$${totalDebtValue.toFixed(2)}</strong>. Consider a debt repayment strategy.`,
                icon: 'fas fa-hand-holding-usd'
            });
        } else if (totalDebtValue > highDebtThresholdWarning) {
            activeAlerts.push({
                type: 'warning',
                message: `<strong>Moderate Debt Alert:</strong> Your total debt is <strong>$${totalDebtValue.toFixed(2)}</strong>. Keep an eye on your balances.`,
                icon: 'fas fa-hand-holding-usd'
            });
        }

        // 6. Savings Below Emergency Fund Target (New Creative Alert)
        // This requires `total_current_savings` and `emergency_fund_target` from Flask.
        // For now, let's assume `total_current_savings` is `total_assets` passed from dashboard and a fixed target.
        const totalCurrentSavingsValue = savingsGoals.reduce((sum, goal) => sum + goal.current_amount, 0);
        // You would ideally pass `average_monthly_expenses` from Flask to calculate this.
        // Let's use a dummy value for average monthly expenses for demonstration if not passed.
        // For a more robust solution, ensure `average_monthly_expenses` is passed to dashboard route and then to initializeAlerts.
        // const averageMonthlyExpenses = {{ average_monthly_expenses | default(0) | tojson }}; // Assuming it's passed
        const averageMonthlyExpenses = 1500; // Placeholder if not passed for this alert
        const emergencyFundTarget = averageMonthlyExpenses * 3; // 3 months coverage

        if (totalCurrentSavingsValue < emergencyFundTarget) {
            const shortfall = emergencyFundTarget - totalCurrentSavingsValue;
            activeAlerts.push({
                type: 'warning',
                message: `<strong>Emergency Fund Low:</strong> You have <strong>$${totalCurrentSavingsValue.toFixed(2)}</strong> saved, but your emergency fund target is <strong>$${emergencyFundTarget.toFixed(2)}</strong> (3 months expenses). You need <strong>$${shortfall.toFixed(2)}</strong> more.`,
                icon: 'fas fa-shield-alt'
            });
        } else {
            activeAlerts.push({
                type: 'success',
                message: `<strong>Emergency Fund Healthy:</strong> You have <strong>$${totalCurrentSavingsValue.toFixed(2)}</strong> in your emergency fund, meeting or exceeding your target!`,
                icon: 'fas fa-heart-pulse'
            });
        }


        // Populate modal body
        if (activeAlerts.length > 0) {
            activeAlerts.forEach(alert => {
                const alertDiv = document.createElement('div');
                alertDiv.className = `alert alert-${alert.type} d-flex align-items-center py-2 mb-2`;
                alertDiv.setAttribute('role', 'alert');
                alertDiv.innerHTML = `<i class="${alert.icon} fs-4 me-3"></i> <div>${alert.message}</div>`;
                alertsModalBody.appendChild(alertDiv);
            });
        } else {
            alertsModalBody.innerHTML = `<div class="alert alert-success text-center" role="alert">
                                            <i class="fas fa-check-circle me-2"></i> All good! No immediate alerts.
                                        </div>`;
        }

        // Update badge
        updateAlertBadge();
    };

    function updateAlertBadge() {
        if (alertBadge) {
            if (activeAlerts.length > 0) {
                alertBadge.textContent = activeAlerts.length;
                alertBadge.classList.remove('d-none'); // Show badge
            } else {
                alertBadge.classList.add('d-none'); // Hide badge
            }
        }
    }
});

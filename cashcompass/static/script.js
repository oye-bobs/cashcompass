/*
 * Custom JavaScript for CashCompass Application.
 * Handles sidebar toggling, navigation highlighting,
 * alert fetching and display, and password visibility toggles.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Instantiate the main application class
    const app = new CashCompassApp();
});


class CashCompassApp {
    constructor() {
        // Initialize core UI components and features
        this.userCollapsed = false; // New state to track if sidebar is explicitly collapsed by user click
        this.alertsModalBody = document.getElementById('alertsModalBody'); // Moved here for class scope
        this.alertBadge = document.getElementById('alertBadge'); // Moved here for class scope

        this.initializeSidebar();
        this.initializeNavigation();
        this.initializeAlerts(); // Global Alerts for the bell icon modal
        this.initializeFlashMessages(); // Auto-dismissing general flash messages
        this.initializePasswordToggles(); // Handles show/hide password functionality
    }

    /**
     * Initializes sidebar toggle functionality and responsive behavior.
     * Manages two states:
     * 1. Desktop: Full sidebar vs. Icons-only collapsed sidebar.
     * 2. Mobile: Sidebar completely hidden vs. overlaying content.
     */
    initializeSidebar() {
        const sidebarToggle = document.getElementById('sidebarToggle');
        const sidebar = document.getElementById('sidebar');
        const mainContentWrapper = document.getElementById('mainContentWrapper');

        if (!sidebarToggle || !sidebar || !mainContentWrapper) {
            console.error('Sidebar elements not found. Ensure #sidebarToggle, #sidebar, and #mainContentWrapper exist.');
            return;
        }

        // Function to set the sidebar state based on screen width
        const setSidebarState = () => {
            if (window.innerWidth > 768) {
                // Desktop view
                sidebar.classList.remove('show'); // Ensure mobile 'show' class is off

                if (this.userCollapsed) {
                    // If user explicitly collapsed it, keep it collapsed
                    sidebar.classList.add('collapsed');
                    mainContentWrapper.classList.add('sidebar-collapsed-view');
                } else {
                    // Otherwise, ensure it's expanded by default on desktop
                    sidebar.classList.remove('collapsed');
                    mainContentWrapper.classList.remove('sidebar-collapsed-view');
                }
            } else {
                // Mobile view
                sidebar.classList.add('collapsed'); // Always collapsed (off-screen) by default on mobile
                sidebar.classList.remove('show'); // Ensure it's hidden initially
                mainContentWrapper.classList.remove('sidebar-collapsed-view'); // Main content is never shifted on mobile
                this.userCollapsed = false; // Reset userCollapsed state for mobile
            }
        };

        // Set initial state on page load
        setSidebarState();

        // Adjust state on window resize
        window.addEventListener('resize', setSidebarState);

        // Toggle sidebar on button click
        sidebarToggle.addEventListener('click', (event) => {
            event.stopPropagation(); // Prevent document click from immediately closing (if on mobile)

            if (window.innerWidth <= 768) {
                // Mobile behavior: Toggle 'show' class to slide in/out
                sidebar.classList.toggle('show');
                // Ensure collapsed class is present for mobile to move it off-screen initially
                sidebar.classList.add('collapsed');
                mainContentWrapper.classList.remove('sidebar-collapsed-view'); // Main content does not shift on mobile
                this.userCollapsed = false; // Reset userCollapsed state for mobile
            } else {
                // Desktop behavior: Toggle 'collapsed' class for icons-only view
                this.userCollapsed = !this.userCollapsed; // Toggle the user-initiated collapse state
                sidebar.classList.toggle('collapsed', this.userCollapsed); // Apply 'collapsed' based on userCollapsed
                mainContentWrapper.classList.toggle('sidebar-collapsed-view', this.userCollapsed); // Shift main content
                sidebar.classList.remove('show'); // Ensure mobile state is off
            }
        });

        // Hover functionality for desktop only, when not explicitly collapsed by user
        sidebar.addEventListener('mouseenter', () => {
            if (window.innerWidth > 768 && !this.userCollapsed) {
                sidebar.classList.remove('collapsed');
                mainContentWrapper.classList.remove('sidebar-collapsed-view');
            }
        });

        sidebar.addEventListener('mouseleave', () => {
            if (window.innerWidth > 768 && !this.userCollapsed) {
                sidebar.classList.add('collapsed');
                mainContentWrapper.classList.add('sidebar-collapsed-view');
            }
        });

        // Close mobile sidebar when clicking outside
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768 &&
                sidebar.classList.contains('show') && // If mobile sidebar is currently shown
                !sidebar.contains(e.target) && // And click is not inside the sidebar
                !sidebarToggle.contains(e.target)) { // And click is not on the toggle button itself

                sidebar.classList.remove('show'); // Hide it
            }
        });
    }

    /**
     * Highlights the active navigation link based on the current URL path.
     */
    initializeNavigation() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.sidebar .nav-link');

        navLinks.forEach(link => {
            link.classList.remove('active'); // Remove active from all first
            // Check if href matches current path, or if it's the root path '/'
            if (link.getAttribute('href') === currentPath ||
                (currentPath === '/' && link.getAttribute('href') === '/')) {
                link.classList.add('active'); // Add active to the matching link
            }
        });
    }

    /**
     * Initializes the alerts system, including fetching, displaying,
     * and handling dismissal/reset actions.
     */
    initializeAlerts() {
        const alertsButton = document.getElementById('alertsButton');
        const alertsModal = document.getElementById('alertsModal');
        const resetAlertsButton = document.getElementById('resetAlertsButton');

        // this.alertsModalBody and this.alertBadge are already defined in constructor

        this.activeAlerts = []; // Array to hold currently active (non-dismissed) alerts

        // Attach event listener to the alerts modal to fetch alerts when shown
        if (alertsModal) {
            alertsModal.addEventListener('show.bs.modal', () => this.fetchAndDisplayAlerts());
            // Optionally re-fetch on hide to ensure badge is always up-to-date
            alertsModal.addEventListener('hidden.bs.modal', () => this.fetchAndDisplayAlerts());
        }

        // Attach event listener for the reset alerts button
        if (resetAlertsButton) {
            resetAlertsButton.addEventListener('click', () => this.resetDismissedAlerts());
        }

        // Initial fetch on page load to update the bell badge count
        this.fetchAndDisplayAlerts();
    }

    /**
     * Fetches financial alerts from the backend API and updates the modal and badge.
     */
    async fetchAndDisplayAlerts() {
        if (!this.alertsModalBody) {
            console.warn('Alerts modal body element not found.');
            return;
        }

        // Show a loading indicator
        this.alertsModalBody.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading alerts...</span>
                </div>
                <p class="mt-2 text-muted">Loading your financial insights...</p>
            </div>
        `;

        try {
            const response = await fetch('/api/financial_alerts_data');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            // The backend now sends only non-dismissed alerts
            this.activeAlerts = await response.json();

            // Clear loading indicator
            this.alertsModalBody.innerHTML = '';

            if (this.activeAlerts.length > 0) {
                this.activeAlerts.forEach(alert => {
                    const alertDiv = document.createElement('div');
                    // Add border-start and custom border classes
                    alertDiv.className = `alert alert-${alert.type} d-flex align-items-center py-2 mb-2 rounded-lg border-start border-4 border-${alert.type}`;
                    alertDiv.setAttribute('role', 'alert');

                    const messageContent = document.createElement('div');
                    messageContent.classList.add('flex-grow-1');
                    // Use alert.message directly as it already contains the icon via Jinja/Flask logic (e.g., strong tags)
                    // If your Python helper includes the icon HTML, remove this: `<i class="${alert.icon} fs-4 me-3"></i>`
                    messageContent.innerHTML = `<i class="${alert.icon} fs-4 me-3"></i> ${alert.message}`;


                    const actionsContainer = document.createElement('div');
                    actionsContainer.classList.add('d-flex', 'align-items-center', 'ms-auto');

                    const isGenericNoAlertsMessage = alert.message === "You have no alerts for now.";

                    // Only make clickable for visual read state if it's a real alert
                    if (!isGenericNoAlertsMessage) {
                        alertDiv.style.cursor = 'pointer';
                        alertDiv.addEventListener('click', (event) => {
                            // Prevent marking as read if the delete button was clicked
                            if (!alertDiv.classList.contains('alert-read') && !event.target.closest('.delete-button-container')) {
                                alertDiv.classList.add('alert-read'); // Visual "read" state
                                alert.is_read_local = true; // Mark as read in our local array
                                this.updateAlertBadge(); // Update the badge count
                                console.log(`Alert marked as read (visually): ${alert.message}`);
                            }
                        });

                        // Add Delete button only for actual alerts
                        const deleteButtonContainer = document.createElement('div');
                        deleteButtonContainer.className = 'delete-button-container ms-2';
                        const deleteButton = document.createElement('button');
                        deleteButton.className = 'delete-button';
                        deleteButton.innerHTML = '<i class="fas fa-trash-alt"></i>';
                        deleteButton.title = 'Dismiss Alert';
                        deleteButton.addEventListener('click', async (event) => {
                            event.stopPropagation(); // Prevent alertDiv click from firing
                            try {
                                // Corrected API endpoint to /api/delete_alert
                                const deleteResponse = await fetch('/api/delete_alert', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ alert_hash: alert.alert_hash })
                                });

                                if (!deleteResponse.ok) {
                                    throw new Error(`Failed to dismiss alert: ${deleteResponse.status}`);
                                }

                                const result = await deleteResponse.json();
                                if (result.success) {
                                    alertDiv.remove(); // Remove alert from DOM
                                    // Remove from local array and update badge
                                    this.activeAlerts = this.activeAlerts.filter(a => a.alert_hash !== alert.alert_hash);
                                    this.updateAlertBadge();

                                    // If no real alerts left after dismissal, show the "no alerts" message
                                    if (this.activeAlerts.filter(a => a.message !== "You have no alerts for now.").length === 0) {
                                        this.alertsModalBody.innerHTML = `
                                            <div class="alert alert-success text-center" role="alert">
                                                <i class="fas fa-check-circle me-2"></i> You have no alerts for now.
                                            </div>
                                        `;
                                    }
                                    console.log(`Alert dismissed: ${alert.message}`);
                                } else {
                                    console.error('Backend reported failure to dismiss alert:', result.message);
                                }
                            } catch (error) {
                                console.error('Error dismissing alert via API:', error);
                            }
                        });
                        deleteButtonContainer.appendChild(deleteButton);
                        actionsContainer.appendChild(deleteButtonContainer);
                    }

                    alertDiv.appendChild(messageContent);
                    alertDiv.appendChild(actionsContainer);
                    this.alertsModalBody.appendChild(alertDiv);

                    // Initialize local read status for badge counting (all new alerts are unread)
                    alert.is_read_local = false;
                });
            } else {
                // Display the "No alerts" message if no alerts are active
                this.alertsModalBody.innerHTML = `
                    <div class="alert alert-success text-center" role="alert">
                        <i class="fas fa-check-circle me-2"></i> You have no alerts for now.
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error fetching financial alerts:', error);
            this.alertsModalBody.innerHTML = `
                <div class="alert alert-danger text-center" role="alert">
                    <i class="fas fa-exclamation-circle me-2"></i> Failed to load alerts. Please try again later.
                </div>
            `;
            this.activeAlerts = []; // Clear alerts on error
        } finally {
            this.updateAlertBadge(); // Always update badge based on current active alerts
        }
    }

    /**
     * Updates the unread alerts badge count in the navbar.
     */
    updateAlertBadge() {
        if (this.alertBadge) {
            // Count alerts that are NOT the generic "no alerts for now" message AND are NOT locally marked as read
            const unreadCount = this.activeAlerts.filter(
                alert => alert.message !== "You have no alerts for now." && !alert.is_read_local
            ).length;

            if (unreadCount > 0) {
                this.alertBadge.textContent = unreadCount;
                this.alertBadge.classList.remove('d-none'); // Show badge
            } else {
                this.alertBadge.classList.add('d-none'); // Hide badge
            }
        }
    }

    /**
     * Resets all dismissed alerts by making an API call to the backend.
     */
    async resetDismissedAlerts() {
        // No confirmation dialog as per user request
        try {
            const response = await fetch('/api/reset_alerts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            if (result.success) {
                console.log(result.message);
                // Re-fetch and display alerts after successful reset
                this.fetchAndDisplayAlerts();
            } else {
                console.error('Backend reported failure to reset alerts:', result.message);
                // Optionally show a user-friendly message for backend errors
            }
        } catch (error) {
            console.error('Error resetting alerts via API:', error);
            // Optionally show a user-friendly error message
            if (this.alertsModalBody) {
                this.alertsModalBody.innerHTML = `
                    <div class="alert alert-danger text-center" role="role">
                        <i class="fas fa-exclamation-circle me-2"></i> Failed to reset alerts. Please try again.
                    </div>
                `;
            }
        }
    }

    /**
     * Initializes functionality for showing/hiding password input fields.
     */
    initializePasswordToggles() {
        // Login and Register page toggles
        this._setupPasswordToggle('togglePassword', 'password', 'passwordEyeIcon');
        // The 'confirmation' ID for the register page is also used on the settings page for 'Confirm New Password'
        this._setupPasswordToggle('toggleConfirmation', 'confirmation', 'confirmationEyeIcon');

        // Profile/Settings page toggles
        // Correcting the input field IDs to match settings.html
        this._setupPasswordToggle('toggleCurrentPassword', 'current_password', 'currentPasswordEyeIcon');
        this._setupPasswordToggle('toggleNewPassword', 'new_password', 'newPasswordEyeIcon');
        // The 'confirmation' toggle is already handled above for the settings page as well.
    }

    /**
     * Helper function to set up a single password toggle.
     * @param {string} toggleButtonId - The ID of the button that toggles visibility.
     * @param {string} inputFieldId - The ID of the password input field.
     * @param {string} iconId - The ID of the icon element within the toggle button.
     */
    _setupPasswordToggle(toggleButtonId, inputFieldId, iconId) {
        const toggleButton = document.getElementById(toggleButtonId);
        const inputField = document.getElementById(inputFieldId);
        const icon = document.getElementById(iconId);

        if (toggleButton && inputField && icon) {
            toggleButton.addEventListener('click', function() {
                const type = inputField.getAttribute('type') === 'password' ? 'text' : 'password';
                inputField.setAttribute('type', type);
                icon.classList.toggle('fa-eye');
                icon.classList.toggle('fa-eye-slash');
            });
        } else {
            // Log a warning if elements are not found, but don't stop execution
            // This is expected because these elements only exist on specific pages (login/register/profile)
            console.warn(`Password toggle elements not found for ${inputFieldId}. This is expected if not on a relevant page.`);
        }
    }

    /**
     * Manages the display and auto-dismissal of Flask flashed messages.
     */
    initializeFlashMessages() {
        // Correctly target the flash messages container by its class name
        const flashMessagesContainer = document.querySelector('.flash-messages-container');
        if (flashMessagesContainer) {
            const alerts = flashMessagesContainer.querySelectorAll('.alert');
            alerts.forEach(alertElement => {
                // Auto-dismiss after 5 seconds (5000 ms) as per the initial request.
                // You can adjust this time if needed.
                setTimeout(() => {
                    // Use Bootstrap's native dismiss if available, otherwise just remove from DOM
                    const bsAlert = bootstrap.Alert.getInstance(alertElement);
                    if (bsAlert) {
                        bsAlert.dispose();
                    } else {
                        alertElement.remove();
                    }
                }, 5000);
            });
        }
    }
}

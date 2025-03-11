// Client-side JavaScript functions for the dashboard

if (!window.dash_clientside) {
    window.dash_clientside = {};
}

// Register the clientside namespace
window.dash_clientside.clientside = {
    /**
     * Refreshes the entire page
     * @param {number} n_clicks - Click count from the refresh button
     * @returns {number} - Random number to trigger the callback
     */
    refreshPage: function(n_clicks) {
        if (n_clicks) {
            console.log("Refreshing page...");
            window.location.reload();
            return Math.random();
        }
        return window.dash_clientside.no_update;
    }
};

// Utility functions
document.addEventListener('DOMContentLoaded', function() {
    console.log("Dashboard client-side scripts initialized");
}); 
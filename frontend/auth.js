"use strict";

const AUTH_API_BASE = window.location.origin;

function logAuthActivity(action, details = "") {
    const timestamp = new Date().toISOString();
    console.log(`[AUTH LOG] ${timestamp} | ACTION: ${action} | ${details}`);
}

function getAccessToken() {
    return localStorage.getItem("gitaToken");
}

function getRefreshToken() {
    return localStorage.getItem("gitaRefreshToken");
}

function setTokens(access, refresh) {
    if (access) localStorage.setItem("gitaToken", access);
    if (refresh) localStorage.setItem("gitaRefreshToken", refresh);
}

function logout() {
    logAuthActivity("logout", "User initiated logout or session invalidated.");
    localStorage.removeItem("gitaToken");
    localStorage.removeItem("gitaRefreshToken");
    localStorage.removeItem("gitaUser");
    window.location.replace("signup.html");
}

// Check if a JWT is expired by parsing its payload
function isTokenExpired(token) {
    if (!token) return true;
    try {
        const payloadBase64 = token.split('.')[1];
        const decodedJson = atob(payloadBase64);
        const payload = JSON.parse(decodedJson);
        const exp = payload.exp;
        const currentSeconds = Math.floor(Date.now() / 1000);
        // Add a 60-second buffer
        return currentSeconds >= (exp - 60);
    } catch (e) {
        return true;
    }
}

async function refreshAccessToken() {
    logAuthActivity("refresh_attempt", "Attempting to refresh access token.");
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
        logAuthActivity("refresh_failure", "No refresh token available.");
        return false;
    }

    try {
        const response = await fetch(`${AUTH_API_BASE}/refresh`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: refreshToken })
        });

        if (!response.ok) {
            logAuthActivity("refresh_failure", `Server rejected refresh token (Status: ${response.status}).`);
            return false;
        }

        const data = await response.json();
        setTokens(data.access_token, data.refresh_token);
        logAuthActivity("refresh_success", "Successfully acquired new access token.");
        return true;
    } catch (err) {
        logAuthActivity("refresh_error", `Network or server error during refresh: ${err}`);
        return false;
    }
}

// Global Auth Guard to wrap page initialization
async function requireAuth(onSuccessCallback) {
    // 1. Create and show loading screen overlay
    let overlay = document.getElementById("globalAuthOverlay");
    if (!overlay) {
        overlay = document.createElement("div");
        overlay.id = "globalAuthOverlay";
        Object.assign(overlay.style, {
            position: "fixed",
            inset: "0",
            backgroundColor: "#020617",
            color: "#facc15",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            zIndex: "99999",
            fontFamily: "'Segoe UI', system-ui, sans-serif",
            fontSize: "20px"
        });
        
        overlay.innerHTML = `
            <div style="width:40px;height:40px;border:4px solid #facc15;border-top:4px solid transparent;border-radius:50%;animation:spin 1s linear infinite;margin-bottom:16px;"></div>
            <style>@keyframes spin { 100% { transform: rotate(360deg); } }</style>
            <div>Verifying session...</div>
        `;
        document.body.appendChild(overlay);
    }
    
    // Hide main app content while verifying
    const appBody = document.querySelector(".app") || document.querySelector(".dashboard-wrapper") || document.querySelector(".chat-wrapper");
    if (appBody) appBody.style.visibility = "hidden";

    const accessToken = getAccessToken();
    const isExpired = isTokenExpired(accessToken);

    if (isExpired) {
        logAuthActivity("auth_check", "Access token is missing or expired. Triggering refresh.");
        const refreshed = await refreshAccessToken();
        if (!refreshed) {
            logout();
            return; // Stop execution
        }
    } else {
        logAuthActivity("auth_check", "Access token is valid.");
    }

    // Success! Remove loading screen and show app
    overlay.remove();
    if (appBody) appBody.style.visibility = "visible";
    
    // Execute the page-specific initialization logic
    if (typeof onSuccessCallback === "function") {
        onSuccessCallback();
    }
}

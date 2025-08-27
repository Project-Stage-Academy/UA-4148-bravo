import Cookies from "js-cookie";
import { api } from './client';

export const CSRF_COOKIE_NAME = "csrftoken";

// How long do we consider cookies to be valid?
export const CSRF_REFRESH_THRESHOLD_MINUTES = 5;

/**
 * Checking whether there is a CSRF token and whether it will expire soon
 */
function needsCsrfRefresh() {
    const token = Cookies.get(CSRF_COOKIE_NAME);
    if (!token) return true; // there is no token at all
    return false; // no need to refresh
}

/**
 * Getter for CSRF
 * URL: /api/v1/csrf
 * Req: {  }
 * Res: 200 { csrfToken }
 */
export async function fetchCsrfToken() {
    try {
        await api.get("/api/v1/auth/csrf");
    } catch (err) {
        console.error("Error when requesting a CSRF token:", err);
    }
}

/**
 * CSRF initialization: if there is no token, or it has expired, obtain a new one
 */
export async function initCsrf() {
    if (needsCsrfRefresh()) {
        await fetchCsrfToken();
    }
}

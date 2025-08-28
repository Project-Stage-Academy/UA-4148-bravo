import axios from "axios";
import Cookies from "js-cookie";
import { CSRF_COOKIE_NAME, fetchCsrfToken } from './csrfService';

/**
 * Creates an isolated API instance with support for single-flight refresh
 */
function createApiClient() {
    /**
     * single-flight refresh
     * @type {Promise<string | null> | null}
     */
    let refreshing = null;

    /**
     * Refreshes access-token by refresh-token
     * @returns {Promise<string | null>} New access token or null
     * if no update is possible
     */
    const refreshAccess = async () => {
        try {
            const res = await axios.post(
                `${process.env.REACT_APP_API_URL}/api/v1/auth/jwt/refresh/`
            );

            if (res.data && typeof res.data.access === "string" && res.data.access.trim() !== "") {
                return res.data.access;
            } else {
                console.warn("[refreshAccess] No access token in API response", res.data);
                return null;
            }
        } catch (err) {
            console.error("[refreshAccess] Failed to refresh access token", err);
            return null;
        }
    }

    // New instance
    const instance = axios.create({
        baseURL: process.env.REACT_APP_API_URL,
        withCredentials: true
    });

    // 401 handler (access token refresh)
    instance.interceptors.response.use(
        r => r,
        async (err) => {
            const original = err.config;

            if (err.response?.status === 401 && !original._retryAuth) {
                original._retryAuth = true;
                console.error("[refreshAccess] Refreshing access token", err);
                refreshing ??= refreshAccess().finally(() => (refreshing = null));

                const newAccess = await refreshing;

                if (newAccess) {
                    return instance(original);
                }
            }

            return Promise.reject(err);
        }
    );

    // 403 handler (CSRF refresh)
    instance.interceptors.response.use(
        r => r,
        async (err) => {
            const original = err.config;

            if (err.response?.status === 403 && !original._retryCsrf) {
                original._retryCsrf = true;
                console.error("[refreshAccess] Refreshing CSRF", err);
                refreshing ??= fetchCsrfToken().finally(() => (refreshing = null));

                const newCsrf = await refreshing;

                if (newCsrf) {
                    return instance(original);
                }
            }

            return Promise.reject(err);
        }
    );

    // CSRF set header if needed
    instance.interceptors.request.use(
        (config) => {
            const method = config.method?.toUpperCase();
            if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
                const csrfToken = Cookies.get(CSRF_COOKIE_NAME);
                if (csrfToken) {
                    config.headers["X-CSRFToken"] = csrfToken;
                }
            }
            return config;
        },
        error => Promise.reject(error)
    );

    return instance;
}

export const api = createApiClient();

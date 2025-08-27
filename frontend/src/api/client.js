import axios from "axios";
import Cookies from "js-cookie";
import { CSRF_COOKIE_NAME } from './csrfService';

/**
 * Access token is used to keep user session active
 * @type {string|null}
 */
let accessToken = null;

/**
 * Setter for access token
 * @param {string|null} value
 */
export const setAccessToken = (value) => {
    accessToken = value;
}

/**
 * Getter for access token
 * @returns {string|null}
 */
export const getAccessToken = () => accessToken

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
                `${process.env.REACT_APP_API_URL}/auth/jwt/refresh/`
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

    // Request interceptor
    instance.interceptors.request.use((cfg) => {
        if (accessToken) cfg.headers.Authorization = `Bearer ${accessToken}`;
        return cfg;
    });

    // Response interceptor
    instance.interceptors.response.use(
        (config) => {
            const method = config.method?.toUpperCase();
            if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
                const csrfToken = Cookies.get(CSRF_COOKIE_NAME);
                if (csrfToken) {
                    config.headers["X-CSRFToken"] = csrfToken;
                }
            }

            config.withCredentials = true;
            return config;
        },
        async (err) => {
            const original = err.config;

            if (err.response?.status === 401 && !original._retry) {
                original._retry = true;
                refreshing ??= refreshAccess().finally(() => (refreshing = null));

                const newAccess = await refreshing;

                if (newAccess) {
                    setAccessToken(newAccess);
                    return instance(original);
                }
            }

            return Promise.reject(err);
        }
    );

    return instance;
}

export const api = createApiClient();

import axios from "axios";

export const api = axios.create({
    baseURL: process.env.REACT_APP_API_URL,
});

/**
 * @type {string | null}
 */
let accessTokenMemory = null;

/**
 * @param {string | null} t
 * @returns {string}
 */
export const setAccessToken = (t) => (accessTokenMemory = t);

api.interceptors.request.use((cfg) => {
    if (accessTokenMemory) cfg.headers.Authorization = `Bearer ${accessTokenMemory}`;
    return cfg;
});


/**
 * single-flight refresh
 * @type {Promise<string | null> | null}
 */
let refreshing = null;

/**
 *
 * @returns {Promise<string | null>}
 */
async function refreshAccess() {
    const refresh = localStorage.getItem("refresh_token");
    if (!refresh) return null;
    const res = await axios.post(`${process.env.REACT_APP_API_URL}/auth/jwt/refresh/`, { refresh });
    return res.data.access;
}

api.interceptors.response.use(
    r => r,
    async (err) => {
        const original = err.config;
        if (err.response?.status === 401 && !original._retry) {
            original._retry = true;
            refreshing ??= refreshAccess().finally(() => (refreshing = null));
            const newAccess = await refreshing;
            if (newAccess) {
                setAccessToken(newAccess);
                return api(original);
            }
        }
        return Promise.reject(err);
    }
);

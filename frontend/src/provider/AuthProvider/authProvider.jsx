import { createContext, useContext, useEffect, useState } from "react";
import { api, setAccessToken } from "../../api/client";
import PropTypes from 'prop-types';

/**
 * @typedef {Object} User - Represents a user in the application
 * @property {number} id - Unique identifier for the user
 * @property {string} name - Name of the user
 * @property {string | null} role - Role of the user (e.g., 'admin', 'user')
 */

/**
 * @typedef {Object} Ctx
 * @property {User | null} user
 * @property {(e: string, p: string) => Promise<void>} login
 * @property {(data: {email:string;password:string;first_name?:string;last_name?:string}) => Promise<void>} register
 * @property {() => void} logout
 * @property {(email: string) => Promise<void>} requestReset
 * @property {(uid: string, token: string, newPassword: string) => Promise<void>} confirmReset
 */

/** @type {import('react').Context<Ctx | null>} */
const AuthCtx = createContext(null);

/**
 * Hook to access the authorization provider.
 * @returns {Ctx | null}
 */
const useAuth = () => useContext(AuthCtx);

/**
 * Authorization Context Provider.
 * Environments the application and provides access to the authorization state.
 * @param {{ children: import('react').ReactNode }} props
 * @returns {JSX.Element}
 */
function AuthProvider({ children }) {
    const [user, setUser] = useState(null);

    /**
     * Sign up: POST /api/v1/auth/register/
     *
     * Body: { email, password, first_name, last_name } --> 201 {id,email}
     *
     * @param {string} email
     * @param {string} password
     * @param {string | null} first_name
     * @param {string | null} last_name
     */
    async function signUp(email, password, first_name, last_name) {
        await api.post("/api/v1/auth/register/", { email, password, first_name, last_name });
    }

    /**
     * Log in (SimpleJWT): POST /api/v1/auth/jwt/create/
     *
     * Body: { email, password } → 200 { access, refresh }
     *
     * @param {string} email
     * @param {string} password
     * @returns {Promise<void>}
     */
    async function login(email, password) {
        const { data } = await api.post("/api/v1/auth/jwt/create/", { email, password });
        localStorage.setItem("refresh_token", data.refresh);
        setAccessToken(data.access);
        await loadUser();
    }

    /**
     * Me: GET /api/v1/auth/me/
     *
     * (optional but recommended) → 200 { id, email, role, ... }
     *
     * @returns {Promise<void>}
     */
    async function loadUser() {
        try {
            const { data } = await api.get("/api/v1/auth/me/");
            setUser(data);
        } catch { setUser(null); }
    }

    /**
     * Log out: client-side (drop tokens).
     *
     * If BE supports blacklist: POST /api/v1/auth/jwt/blacklist/ { refresh } → 205
     */
    function logout() {
        const refresh = localStorage.getItem("refresh_token");
        if (refresh) { api.post("/api/v1/auth/jwt/blacklist/", { refresh }).catch(() => {}); }
        localStorage.removeItem("refresh_token");
        setAccessToken(null);
        setUser(null);
    }

    /**
     * Password reset request: POST /api/v1/auth/password/reset/
     *
     * Body: { email } → 200
     *
     * @param {string} email
     * @returns {Promise<void>}
     */
    async function requestReset(email) {
        await api.post("/api/v1/auth/password/reset/", { email });
    }

    /**
     * Password reset confirm: POST /api/v1/auth/password/reset/confirm/
     *
     * Body: { uid, token, new_password } → 200
     *
     * @param {string} uid
     * @param {string} token
     * @param {string} new_password
     * @returns {Promise<void>}
     */
    async function confirmReset(uid, token, new_password) {
        await api.post("/api/v1/auth/password/reset/confirm/", { uid, token, new_password });
    }

    /**
     * Refresh: POST /api/v1/auth/jwt/refresh/
     *
     * Body: { refresh } → 200 { access }
     */
    useEffect(() => {
        (async () => {
            const refresh = localStorage.getItem("refresh_token");
            if (!refresh) return;
            try {
                const { data } = await api.post("/api/v1/auth/jwt/refresh/", { refresh });
                setAccessToken(data.access);
                await loadUser();
            } catch {
                logout();
            }
        })();
    }, []);

    return (
        <AuthCtx.Provider value={{ user, login, register: signUp, logout, requestReset, confirmReset }}>
            {children}
        </AuthCtx.Provider>
    );
}

AuthProvider.propTypes = {
    children: PropTypes.node.isRequired,
};

export { useAuth };
export default AuthProvider;

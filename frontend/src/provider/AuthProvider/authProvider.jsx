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

    async function loadUser() {
        try {
            const { data } = await api.get("/auth/me/");
            setUser(data);
        } catch { setUser(null); }
    }

    async function login(email, password) {
        const { data } = await api.post("/auth/jwt/create/", { email, password });
        localStorage.setItem("refresh_token", data.refresh);
        setAccessToken(data.access);
        await loadUser();
    }

    async function register(payload) {
        await api.post("/auth/register/", payload);
        // optional: auto-login after register (if BE returns tokens)
    }

    function logout() {
        const refresh = localStorage.getItem("refresh_token");
        if (refresh) { api.post("/auth/jwt/blacklist/", { refresh }).catch(() => {}); }
        localStorage.removeItem("refresh_token");
        setAccessToken(null);
        setUser(null);
    }

    async function requestReset(email) {
        await api.post("/auth/password/reset/", { email });
    }

    async function confirmReset(uid, token, new_password) {
        await api.post("/auth/password/reset/confirm/", { uid, token, new_password });
    }

    useEffect(() => { // try to restore session on mount
        (async () => {
            const refresh = localStorage.getItem("refresh_token");
            if (!refresh) return;
            try {
                const { data } = await api.post("/auth/jwt/refresh/", { refresh });
                setAccessToken(data.access);
                await loadUser();
            } catch {
                logout();
            }
        })();
    }, []);

    return (
        <AuthCtx.Provider value={{ user, login, register, logout, requestReset, confirmReset }}>
            {children}
        </AuthCtx.Provider>
    );
}

AuthProvider.propTypes = {
    children: PropTypes.node.isRequired,
};

export { useAuth };
export default AuthProvider;

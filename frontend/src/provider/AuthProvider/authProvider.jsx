import {createContext, useCallback, useContext, useMemo, useState} from 'react';
import { api, getAccessToken, setAccessToken } from '../../api/client';
import PropTypes from 'prop-types';
import useProactiveRefresh from '../../hooks/useProactiveRefresh/useProactiveRefresh';

/**
 * @typedef {Object} User - Represents a user in the application
 * @property {number} id - Unique identifier for the user
 * @property {string} first_name - First name of the user
 * @property {string} last_name - Last name of the user
 * @property {string} email - Email of the user
 * @property {string | null} role - Role of the user (e.g., 'admin', 'user')
 */

/**
 * @typedef {Object} Ctx
 * @property {User | null} user
 * @property {(e: string, p: string) => Promise<void>} login
 * @property {(email: string, first_name: string | null, last_name: string | null, password: string, confirmPassword: string)
 * => Promise<void>} register
 * @property {(email: string, userId: number) => Promise<void>} resendRegisterEmail
 * @property {(user_id: number, token: string) => Promise<void>} confirmEmail
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
const useAuthContext = () => useContext(AuthCtx);

/**
 * Authorization Context Provider.
 * Envelops the application and provides access to the authorization state.
 * @param {{ children: import('react').ReactNode }} props
 * @returns {JSX.Element}
 */
function AuthProvider({ children }) {
    const [user, setUser] = useState(null);

    /**
     * Register
     * URL: /api/v1/auth/register/
     * Req: { email, first_name, last_name, password, password2 }
     * Res: 201 { status, message, user_id, email }
     *
     * @param {string} email
     * @param {string | null} first_name
     * @param {string | null} last_name
     * @param {string} password
     * @param {string} confirmPassword
     */
    const register = useCallback(
        async (email, first_name, last_name, password, confirmPassword) => {
            try {
                return await api.post('/api/v1/auth/register/', {
                    email,
                    first_name,
                    last_name,
                    password,
                    password2: confirmPassword,
                });
            } catch (err) {
                console.error(err);
                throw err;
            }
        },
        []
    );

    /**
     * Resend register email
     * URL: /api/v1/auth/register/resend/
     * Req: { email, userId }
     * Res: 201 { status, message, user_id, email }
     *
     * @param {string} email
     * @param {number} userId
     */
    const resendRegisterEmail = useCallback(
        async (email, userId) => {
            await api.post('/api/v1/auth/resend-email/', {
                email: email,
                user_id: userId,
            }).catch((err) => {
                console.error(err);
                throw err;
            });
        }, []
    );

    const confirmEmail = useCallback(
        async (user_id, token) => {
            try {
                console.log("Calling confirmEmail..."); // debug
                await api.get(`/api/v1/auth/verify-email/${user_id}/${token}/`);
            } catch (err) {
                console.error(err);
                throw err;
            }
        },
        []
    );

    /**
     * Create
     * URL: /api/v1/auth/jwt/create/
     * Req: { email, password }
     * Res: 200 { access, refresh }
     *
     * @param {string} email
     * @param {string} password
     * @returns {Promise<void>}
     */
    const login = useCallback(
        async (email, password) => {
            const { data } = await api.post('/api/v1/auth/jwt/create/', {
                email,
                password,
            }).catch((err) => {
                console.error(err);
                throw err;
            });

            if (data.access) {
                console.log('data.access is missing or null');
            }

            setAccessToken(data.access);
            /*
            TODO
            await loadUser();
            */
        }, []
    );

    /**
     * Me
     * URL: /api/v1/auth/me/
     * Req: {}
     * Res: 200 { id, email, role, ... }
     *
     * @returns {Promise<void>}
     */
    const loadUser = useCallback(
        async () => {
            try {
                const { data } = await api.get("/api/v1/auth/me/")
                    .catch((err) => {
                        console.error(err);
                    });
                setUser(data);
            } catch {
                console.log('User not found');
                setUser(null);
            }
        }, []
    );

    /**
     * Logout
     * URL: /api/v1/auth/jwt/logout/
     * Req: { refresh }
     * Res: 205
     */
    const logout = useCallback(
        async () => {
            await api.post("/api/v1/auth/jwt/logout/").catch(() => {
                console.log('Logout');
            });
            setAccessToken(null);
            setUser(null);
        }, []
    );

    /**
     * Password reset
     * URL: /api/v1/auth/password/reset/
     * Req: { email }
     * Res: 200
     *
     * @param {string} email
     * @returns {Promise<void>}
     */
    const requestReset = useCallback(
        async (email) => {
            await api.post("/api/v1/auth/password/reset/", { email }).catch((err) => {
                console.error(err);
            });
        }, []
    );

    /**
     * Password reset confirm
     * URL: /api/v1/auth/password/reset/confirm/
     * Req: { uid, token, new_password }
     * Res: 200
     *
     * @param {string} uid
     * @param {string} token
     * @param {string} new_password
     * @returns {Promise<void>}
     */
    const confirmReset = useCallback(
        async (uid, token, new_password) => {
            await api.post("/api/v1/auth/password/reset/confirm/", { uid, token, new_password }).catch((err) => {
                console.error(err);
            });
        }, []
    );

    /**
     * Refresh
     * URL: /api/v1/auth/jwt/refresh/
     * Req: { refresh }
     * Res: 200 { access }
     */
    const refreshToken = useCallback(
        async () => {
            try {
                const { data } = await api.post("/api/v1/auth/jwt/refresh/");
                setAccessToken(data.access || null);
                /*
                * TODO
                * await loadUser();
                */
            } catch (err) {
                if (err.response) {
                    console.log("Refresh token missing or invalid:", err.response.status);
                } else {
                    console.error(err);
                }

                if (err.response?.status === 401) {
                    await logout();
                }
            }
        }, [setAccessToken, logout]
    );

    useProactiveRefresh(getAccessToken(), refreshToken);

    return (
        <AuthCtx.Provider
            value={useMemo(
                () => ({
                    user,
                    setUser,
                    login,
                    register,
                    resendRegisterEmail,
                    confirmEmail,
                    logout,
                    requestReset,
                    confirmReset
                }),
                [
                    user,
                    setUser,
                    login,
                    register,
                    resendRegisterEmail,
                    confirmEmail,
                    logout,
                    requestReset,
                    confirmReset
                ]
            )}
        >
            {children}
        </AuthCtx.Provider>
    );
}

AuthProvider.propTypes = {
    children: PropTypes.node,
};

AuthProvider.defaultProps = {
    children: null,
};

export { useAuthContext };
export default AuthProvider;

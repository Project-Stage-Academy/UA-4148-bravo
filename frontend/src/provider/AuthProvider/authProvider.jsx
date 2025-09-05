import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useRef,
    useState,
} from 'react';
import { api } from '../../api/client';
import PropTypes from 'prop-types';

/**
 * @typedef {Object} User - Represents a user in the application
 * @property {number} id - Unique identifier for the user
 * @property {string} first_name - First name of the user
 * @property {string} last_name - Last name of the user
 * @property {string} email - Email of the user
 * @property {string | null} role - Role of the user (e.g., 'admin', 'user')
 * @property {string | null} companyType - Type of company
 * @property {number | null} companyId - ID of the company
 * @property {boolean} isAuthorized - Defines if user is authorized for visual context
 */

/**
 * @typedef {Object} Ctx
 * @property {User | null} user
 * @property {(function((User | null)): void)} setUser
 * @property {function(string, string): Promise<AxiosResponse<any>>} login
 * @property {function(string, (string | null), (string | null), string, string): Promise<AxiosResponse<any>>} register
 * @property {function(string, number): Promise<void>} resendRegisterEmail
 * @property {function(number, string): Promise<void>} confirmEmail
 * @property {function(string, ("startup" | "investor")): Promise<void>} bindCompanyToUser
 * @property {function(): Promise<void>} logout
 * @property {function(string): Promise<void>} requestReset
 * @property {function(string, string, string): Promise<void>} confirmReset
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
    const resendRegisterEmail = useCallback(async (email, userId) => {
        await api
            .post('/api/v1/auth/resend-email/', {
                email: email,
                user_id: userId,
            })
            .catch((err) => {
                console.error(err);
                throw err;
            });
    }, []);

    /**
     * Confirm register email
     * URL: /api/v1/auth/verify-email/<int:user_id>/<string:token>/
     * Req: {  }
     * Res: 200
     *
     * @param {number} user_id
     * @param {string} token
     */
    const confirmEmail = useCallback(async (user_id, token) => {
        try {
            await api.get(`/api/v1/auth/verify-email/${user_id}/${token}/`);
        } catch (err) {
            console.error(err);
            throw err;
        }
    }, []);

    /**
     * Enable newly registered users to bind themselves to an existing or new company
     * URL: /api/v1/auth/bind-company/
     * Req: { company_name, company_type }
     * Res: 200
     *
     * @param {string} company_name
     * @param {'startup'|'investor'} company_type
     */
    const bindCompanyToUser = useCallback(
        async (company_name, company_type) => {
            try {
                await api.post(`/api/v1/auth/bind-company/`, {
                    company_name,
                    company_type,
                });
            } catch (err) {
                console.error(err);
                throw err;
            }
        }, []
    );

    /**
     * Me
     * URL: /api/v1/auth/me/
     * Req: {  }
     * Res: 200 { id, email, role, ... }
     *
     * @returns {Promise<void|User>}
     */
    const loadUser = useCallback(async () => {
        try {
            const res = await api.get('/api/v1/auth/me/');
            const data = res.data;

            const newUser = {
                id: data.id || data.user_id,
                email: data.email,
                first_name: data.first_name,
                last_name: data.last_name,
                role: data.role,
                companyType: data.company_type || null,
                companyId: data.company_id || null,
                isAuthorized: true,
            };

            console.log(newUser)
            setUser(newUser);

            if (process.env.REACT_APP_NODE_ENV === 'development') {
                console.log('User is authorized');
            }

            return newUser;
        } catch (err) {
            console.error(err);

            if (err.response?.status === 404) {
                setUser(null);
            } else {
                throw err;
            }

            return null;
        }
    }, []);

    /**
     * Create
     * URL: /api/v1/auth/jwt/create/
     * Req: { email, password }
     * Res: 200 { access, refresh }
     *
     * @param {string} email
     * @param {string} password
     * @returns {Promise<Object<AxiosResponse<any>,User|null>>}
     */
    const login = useCallback(
        async (email, password) => {
            const res = await api
                .post('/api/v1/auth/jwt/create/', {
                    email,
                    password,
                })
                .catch((err) => {
                    console.error(err);
                    throw err;
                });

            const newUser = await loadUser();
            return { res, newUser };
        },
        [loadUser]
    );

    /**
     * Logout
     * URL: /api/v1/auth/logout/
     * Req: {  }
     * Res: 205
     */
    const logout = useCallback(async () => {
        await api
            .post('/api/v1/auth/logout/')
            .then(() => setUser(null))
            .catch((err) => {
                console.log('Logout error\n', err);
                if (err.response?.status === 401) setUser(null);
            });
    }, []);

    /**
     * Password reset
     * URL: /api/v1/auth/password/reset/
     * Req: { email }
     * Res: 200
     *
     * @param {string} email
     * @returns {Promise<void>}
     */
    const requestReset = useCallback(async (email) => {
        return await api
            .post('/api/v1/auth/password/reset/', { email })
            .catch((err) => {
                console.error(err);
                // throw err;
            });
    }, []);

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
    const confirmReset = useCallback(async (uid, token, new_password) => {
        await api
            .post('/api/v1/auth/password/reset/confirm/', {
                uid,
                token,
                new_password,
            })
            .catch((err) => {
                console.error(err);
            });
    }, []);

    /**
     * Refresh
     * URL: /api/v1/auth/jwt/refresh/
     * Req: {  }
     * Res: 200 {  }
     */
    const refreshToken = useCallback(async () => {
        try {
            await api.post('/api/v1/auth/jwt/refresh/');
        } catch (err) {
            if (err.response) {
                console.log(
                    'Refresh token missing or invalid:',
                    err.response.status
                );

                if (err.response?.status === 500) {
                    console.log('Server do not know this token [500]');
                    await logout();
                }

                if (err.response?.status === 404) {
                    console.log('Server do not know this token [404]');
                    await logout();
                }
            } else {
                console.error(err);
            }
            throw err;
        }
    }, [logout]);

    const isRefreshing = useRef(false);
    useEffect(() => {
        if (isRefreshing.current) return;
        isRefreshing.current = true;

        (async () => {
            try {
                await refreshToken();
                await loadUser();
            } catch {
                await logout();
            }
        })();
    });

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
                    bindCompanyToUser,
                    logout,
                    requestReset,
                    confirmReset,
                }),
                [
                    user,
                    setUser,
                    login,
                    register,
                    resendRegisterEmail,
                    confirmEmail,
                    bindCompanyToUser,
                    logout,
                    requestReset,
                    confirmReset,
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

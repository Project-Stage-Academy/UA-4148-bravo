import { createContext, useContext, useState } from 'react';
import PropTypes from 'prop-types';

/**
 * @typedef {Object} AuthContextType
 * @property {*} auth - User authorization data
 * @property {function(*):void} setAuth - Function for updating authorization data
 */

/** @type {import('react').Context<AuthContextType | null>} */
export const AuthContext = createContext(null);

/**
 * Hook to access the authorization context.
 * @returns {AuthContextType | null}
 */
export const useAuth = () => useContext(AuthContext);

/**
 * Authorization Context Provider.
 * Environments the application and provides access to the authorization state.
 * @param {{ children: import('react').ReactNode }} props
 * @returns {JSX.Element}
 */
function AuthProvider({ children }) {
    const [auth, setAuth] = useState(null);

    return (
        <AuthContext.Provider value={{ auth, setAuth }}>
            {children}
        </AuthContext.Provider>
    );
}

AuthProvider.propTypes = {
    children: PropTypes.node.isRequired,
};

export default AuthProvider;

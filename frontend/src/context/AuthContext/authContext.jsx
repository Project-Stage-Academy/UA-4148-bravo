import { createContext, useContext, useState, useEffect } from 'react';
import PropTypes from 'prop-types';

/**
 * @typedef {Object} User - Represents a user in the application
 * @property {string} id - Unique identifier for the user
 * @property {string} name - Name of the user
 * @property {string} role - Role of the user (e.g., 'admin', 'user')
 */

/**
 * @typedef {Object} AuthContextType
 * @property {User | null} user - Current user or null
 * @property {(user: User | null) => void} setUser - Function for user installation
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
    const [user, setUser] = useState(null);

    useEffect(() => {
        // Load user data from localStorage or API
    }, []);

    return (
        <AuthContext.Provider value={{ user, setUser }}>
            {children}
        </AuthContext.Provider>
    );
}

AuthProvider.propTypes = {
    children: PropTypes.node.isRequired,
};

export default AuthProvider;

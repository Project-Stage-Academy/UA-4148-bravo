import { createContext, useContext, useState } from 'react';

/**
 * AuthContext provides a way to manage authentication state across the application.
 * It uses React's Context API to share the authentication state and a function to update it.
 * The context can be used to access the current authentication state and update it from any component within the provider.
 * @type {React.Context<null>}
 */
export const AuthContext = createContext(null);

/**
 * useAuth is a custom hook that provides access to the AuthContext.
 * It allows components to easily access the authentication state and the function to update it.
 * This hook returns the current authentication state and a function to set the authentication state.
 * It is a convenient way to consume the AuthContext without needing to use the Context.Consumer directly
 * @returns {PropTypes.Validator<null | undefined>}
 */
export const useAuth = () => useContext(AuthContext);

/**
 * AuthProvider is a React component that wraps its children with the AuthContext provider.
 * It manages the authentication state using React's useState hook.
 * The provider passes down the current authentication state and a function to update it to all components within
 * the provider.
 * @param children
 * @returns {JSX.Element}
 * @constructor
 */
export function AuthProvider({ children }) {
    const [auth, setAuth] = useState(null);

    return (
        <AuthContext.Provider value={{ auth, setAuth }}>
            {children}
        </AuthContext.Provider>
    );
}

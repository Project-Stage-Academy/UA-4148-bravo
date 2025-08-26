import "./authorizationWrapper.css";
import { Outlet } from 'react-router-dom';

/**
 * AuthorizationWrapper component
 * This component serves as a wrapper for authorization-related pages.
 * It uses React Router's Outlet to render nested routes.
 * @returns {JSX.Element}
 */
function AuthorizationWrapper() {
    return (
        <div className={"authorization-wrapper"}>
            <Outlet />
        </div>
    );
}

export default AuthorizationWrapper;

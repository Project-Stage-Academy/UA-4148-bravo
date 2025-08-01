import "./authorizationWrapper.css";
import { Outlet } from 'react-router-dom';

function AuthorizationWrapper() {
    return (
        <div className={"authorization-wrapper"}>
            <Outlet />
        </div>
    );
}

export default AuthorizationWrapper;

import './requireAuth.css';
import { Navigate, useLocation } from "react-router-dom";

function RequireAuth({ children }) {
    const user = localStorage.getItem("refresh_token");
    const location = useLocation();

    if (!user) {
        return <Navigate to="/auth/login" state={{ from: location }} replace />;
    }

    return children;
}

export default RequireAuth;

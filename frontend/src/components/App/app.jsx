import { BrowserRouter, Route, Routes } from 'react-router-dom';
import React from 'react';
import { AuthProvider } from '../../context/AuthContext/authContext';
import Layout from '../Layout/layout';
import ProfileEditing from '../../pages/ProfileEditing/profileEditing';
import NotFound from '../../pages/NotFound/notFound';
import HomePage from '../../pages/Home/home';
import CompanyList from '../../pages/CompanyList/companyList';
import FeedbackForm from '../../pages/FeedbackForm/feedbackForm';
import ForgotPassword from '../../pages/ForgotPassword/forgotPassword';
import RestorePassword from '../../pages/RestorePassword/restorePassword';
import ProfilePage from '../../pages/ProfilePage/profilePage';
import Policy from '../../pages/Policy/policy';
import WhoWeAre from '../../pages/WhoWeAre/whoWeAre';
import LogInPage from '../../pages/LogIn/logIn';
import RegistrationPage from '../../pages/Registration/registration';

/**
 * Main application component that sets up routing and context providers.
 * It wraps the application in an AuthProvider for authentication context
 * and uses React Router for navigation.
 * The main layout is defined in the Layout component, which includes
 * the header, sidebar, and footer.
 * The Routes define the various pages of the application, including:
 * - Home page
 * - Company list
 * - Feedback form
 * - Policy page
 * - Who we are page
 * - Log in page
 * - Registration page
 * - Password management (forgot and restore)
 * - User and company profile pages with editing capabilities
 * - A catch-all route for 404 Not Found
 * @returns {JSX.Element} The main application component.
 */
function App() {
    return (
        <AuthProvider>
            <React.StrictMode>
                <BrowserRouter>
                    <Routes>

                        {/* Main layout */}
                        <Route path="/" element={<Layout />}>

                            {/* Home page */}
                            <Route index element={<HomePage />} />

                            {/* Company list */}
                            <Route path="companies" element={<CompanyList />} />

                            {/* Feedback form */}
                            <Route path="feedback" element={<FeedbackForm />} />

                            {/* Policy */}
                            <Route path="policy" element={<Policy />} />

                            {/* Who we are */}
                            <Route path="who-we-are" element={<WhoWeAre />} />

                            {/* Log in */}
                            <Route path="login" element={<LogInPage />} />

                            {/* Registration */}
                            <Route path="register" element={<RegistrationPage />} />

                            {/* Password */}
                            <Route path="password">

                                {/* Forgot password */}
                                <Route path="forgot" element={<ForgotPassword />} />

                                {/* Restore password */}
                                <Route path="restore" element={<RestorePassword />} />
                            </Route>

                            {/* Profile */}
                            <Route path="profile">

                                {/* User profile */}
                                <Route path="user" element={<ProfilePage />}>

                                    {/* Profile editing */}
                                    <Route path="edit" element={<ProfileEditing />} />
                                </Route>

                                {/* Company profile */}
                                <Route path="company" element={<ProfilePage />}>

                                    {/* Profile editing */}
                                    <Route path="edit" element={<ProfileEditing />} />
                                </Route>
                            </Route>

                            {/* Page not found */}
                            <Route path="*" element={<NotFound />} />
                        </Route>
                    </Routes>
                </BrowserRouter>
            </React.StrictMode>
        </AuthProvider>
    );
}

export default App;

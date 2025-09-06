import { BrowserRouter, Route, Routes } from 'react-router-dom';
import React from 'react';
import AuthProvider from '../../provider/AuthProvider/authProvider';
import Layout from '../Layout/layout';
import ProfileEditing from '../../pages/ProfileEditing/profileEditing';
import NotFound from '../../pages/NotFound/notFound';
import HomePage from '../../pages/Home/home';
import CompanyList from '../../pages/CompanyList/companyList';
import FeedbackForm from '../../pages/FeedbackForm/feedbackForm';
import ForgotPassword from '../../pages/ForgotPassword/forgotPassword';
import RestorePassword from '../../pages/RestorePassword/restorePassword';
import ProfilePage from '../../pages/ProfilePage/profilePage';
import Policy from '../../pages/Policy/policy.jsx';
import WhoWeAre from '../../pages/WhoWeAre/whoWeAre';
import LogInPage from '../../pages/LogIn/logIn';
import RegistrationPage from '../../pages/Registration/registration';
import AuthorizationWrapper from '../../pages/AuthorizationWrapper/authorizationWrapper';
import RegistrationConfirmation from '../../pages/RegistrationConfirmation/registrationConfirmation';
import RegistrationReconfirmation from '../../pages/RegistrationReconfirmation/registrationReconfirmation';
import RegistrationError from '../../pages/RegistrationError/registrationError';
import RegistrationUserConfirmed from '../../pages/RegistrationUserConfirmed/registrationUserConfirmed';
import EmailConfirmationHandler from '../../pages/EmailConfirmationHandler/emailConfirmationHandler';
import RestorePasswordDone from '../../pages/RestorePasswordDone/restorePasswordDone';
import RegistrationUserRepresent from '../../pages/RegistrationUserRepresent/registrationUserRepresent';
import RegistrationCompleted from '../../pages/RegistrationCompleted/registrationCompleted';
import ForgotPasswordDone from '../../pages/ForgotPasswordDone/forgotPasswordDone';
import PasswordResetHandler from '../../pages/PasswordResetHandler/passwordResetHandler';

/**
 * Main application component that sets up routing and provider providers.
 * It wraps the application in an AuthProvider for authentication provider
 * and uses React Router for navigation.
 * The main layout is defined in the Layout component, which includes
 * the header, sidebar, and footer.
 * The Routes define the various pages of the application, including:
 *
 * @component
 *
 * @returns {JSX.Element} The main application component.
 */
function App() {
    return (
        <AuthProvider>
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

                        {/* Who we are */}
                        <Route path="who-we-are" element={<WhoWeAre />} />

                        <Route path={"auth"} element={<AuthorizationWrapper />}>

                            {/* Log in */}
                            <Route path="login" element={<LogInPage />} />

                            {/* Registration */}
                            <Route path="register" element={<RegistrationPage />} />

                            <Route path="register/confirm" element={<RegistrationConfirmation />} />
                            <Route path="register/re-confirm" element={<RegistrationReconfirmation />} />
                            <Route path="register/error" element={<RegistrationError />} />
                            <Route path="register/user-confirmed" element={<RegistrationUserConfirmed />} />
                            <Route path="register/user-represent" element={<RegistrationUserRepresent />} />
                            <Route path="register/completed" element={<RegistrationCompleted />} />

                            {/* Email verificator */}
                            <Route path="verify-email/:user_id/:token" element={<EmailConfirmationHandler />} />

                            {/* Forgot password */}
                            <Route path="forgot" element={<ForgotPassword />} />
                            <Route path="forgot/done" element={<ForgotPasswordDone />} />

                            {/* Restore password */}
                            <Route path="restore-password" element={<RestorePassword />} />
                            <Route path="restore-password/done" element={<RestorePasswordDone />} />
                        </Route>

                        {/* Profile */}
                        <Route path="profile/:uid" element={<ProfilePage />} >

                            {/* Profile editing */}
                            <Route path="edit" element={<ProfileEditing />} />
                        </Route>

                        {/* Redirect password reset */}
                        <Route path="/password/reset/confirm/:user_id/:token/" element={<PasswordResetHandler />} />
                          
                        {/* Privacy policy */}
                        <Route path="privacy-policy" element={<Policy />} />

                        {/* Page not found */}
                        <Route path="*" element={<NotFound />} />
                    </Route>
                </Routes>
            </BrowserRouter>
        </AuthProvider>
    );
}

export default App;

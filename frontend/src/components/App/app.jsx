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

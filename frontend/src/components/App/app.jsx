import { BrowserRouter, Route, Routes } from 'react-router-dom';
import React from 'react';
import Layout from '../Layout/layout';
import ProfileEditing from '../../pages/ProfileEditing/profileEditing';
import { AuthProvider } from '../../context/AuthContext/authContext';
import NotFound from '../../pages/NotFound/notFound';
import HomePage from '../../pages/Home/home';

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

                            {/* Profile */}
                            <Route path="profile">
                                {/* Profile editing */}
                                <Route path="edit" element={<ProfileEditing />} />
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

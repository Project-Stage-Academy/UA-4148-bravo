import {BrowserRouter, Route, Routes} from "react-router-dom";
import React from "react";
import Layout from "../Layout/layout";
import ProfileEditing from "../../pages/ProfileEditing/profileEditing";

function App() {
    return (
        <React.StrictMode>
            <BrowserRouter>
                <Routes>
                    <Route path="/" element={<Layout />}>
                        <Route path="/" element={<ProfileEditing />}/>
                    </Route>
                </Routes>
            </BrowserRouter>
        </React.StrictMode>
    );
}

export default App;

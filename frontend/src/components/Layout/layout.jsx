import { Outlet } from 'react-router-dom';
import Footer from '../Footer/footer';
import Header from '../Header/header';
import Sidebar from '../Sidebar/sidebar';
import { useState } from 'react';

function Layout() {
    /* Sidebar variables */
    const [dimmerActive, setDimmerActive] = useState(false);
    const showSidebar = () => setDimmerActive(true);
    const hideSidebar = () => setDimmerActive(false);
    const toggleSidebar = () => setDimmerActive(v => !v);

    return (
        <>
            <Header show={showSidebar} hide={hideSidebar} toggle={toggleSidebar} visible={dimmerActive} />
            <Sidebar show={showSidebar} hide={hideSidebar} toggle={toggleSidebar} visible={dimmerActive}>
                <main>
                    <Outlet />
                </main>
                <Footer />
            </Sidebar>
        </>
    );
}

export default Layout;

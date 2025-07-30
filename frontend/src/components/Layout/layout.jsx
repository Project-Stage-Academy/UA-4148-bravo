import { Outlet } from 'react-router-dom';
import Footer from '../Footer/footer';
import Header from '../Header/header';
import Sidebar from '../Sidebar/sidebar';
import { useState } from 'react';

/**
 * Layout component that wraps the main content with Header, Sidebar, and Footer.
 * It manages the visibility of the sidebar using state.
 * The `Header` component provides methods to show, hide, and toggle sidebar.
 * The `Sidebar` component is displayed based on the visibility state.
 * The `Outlet` component renders the child routes within the main content area.
 * This component is used to create a consistent layout across different pages of the application.
 * It allows for a responsive design where the sidebar can be toggled on smaller screens.
 * The useState hook is used to manage the sidebar's visibility state.
 */
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

import { Outlet } from 'react-router-dom';
import Footer from '../Footer/footer';
import Header from '../Header/header';
import Sidebar from '../Sidebar/sidebar';
import { useRef } from 'react';

function Layout() {
    const sidebarDimmerRef = useRef();

    return (
        <>
            <Header visible={sidebarDimmerRef.current?.dimmerActive}
                    onMenuClick={() => sidebarDimmerRef.current?.toggle()} />
            <Sidebar ref={sidebarDimmerRef}>
                <main>
                    <Outlet />
                </main>
                <Footer />
            </Sidebar>
        </>
    );
}

export default Layout;

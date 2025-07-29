import { Outlet } from 'react-router-dom';
import Footer from '../Footer/footer';

function Layout() {
    return (
        <>
            <main>
                <Outlet />
            </main>
            <Footer />
        </>
    );
}

export default Layout;

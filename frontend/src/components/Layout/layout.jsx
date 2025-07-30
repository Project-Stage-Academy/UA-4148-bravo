import { Outlet } from 'react-router-dom';
import Footer from '../Footer/footer';
import Header from '../Header/header';

function Layout() {
    return (
        <>
            <Header />
            <main>
                <Outlet />
            </main>
            <Footer />
        </>
    );
}

export default Layout;

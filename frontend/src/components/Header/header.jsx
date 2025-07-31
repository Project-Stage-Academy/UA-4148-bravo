import "./header.css";
import { Link, useNavigate } from 'react-router-dom';
import Search from "../Search/search";
import {useAuth} from "../../context/AuthContext/authContext";
import { useEffect } from 'react';

/**
 * Header component
 * @param show - function to show the header
 * @param hide - function to hide the header
 * @param toggle - function to toggle the header visibility
 * @param visible - boolean indicating if the header is visible
 * @returns {JSX.Element}
 */
function Header({ show, hide, toggle, visible }) {
    const navigate = useNavigate();
    const { auth, setAuth } = useAuth();

    useEffect(() => {
        setAuth(false);
    }, [auth, setAuth]);

    return (
        <header className={'header'}>
            <Link to={"/"} className={'header--logo'}>
                <img src="/pictures/svg/header-logo.svg" alt={'Logo'} />
                <img
                    src="/pictures/svg/header-logo-text.svg"
                    alt={'Logo text'}
                    className={'header--logo__disposal'}
                />
            </Link>
            <nav className={'nav-panel'}>
                <div className={'nav-panel--set nav-panel--set__disposal'}>
                    <Link to={'/who-we-are'} className={'link__underline nav-panel--link'}>
                        <p>Про нас</p>
                    </Link>
                    <Link to={'/companies'} className={'link__underline nav-panel--link'}>
                        <p>Підприємства та сектори</p>
                    </Link>
                    <Search width={'225px'} />
                </div>
                {auth ? (
                    <div className={'nav-panel--set'}>
                        <Link
                            to={'/profile/user/edit'}
                            className={'nav-panel--link'}
                        >
                            <img
                                src="/pictures/svg/avatar.svg"
                                alt={'User avatar'}
                            />
                            <p>Мій профіль</p>
                        </Link>
                    </div>
                ) : (
                    <div className={'nav-panel--set'}>
                        <Link to={'/login'} className={'link__underline nav-panel--link'}>
                            <p>Увійти</p>
                        </Link>
                        <button
                            className={
                                'button button__padding button__primary-color'
                            }
                            onClick={() => navigate('/register')}
                        >
                            Зареєструватися
                        </button>
                    </div>
                )}
                <button
                    className={
                        'button button__transparent-color nav-panel--menu-btn'
                    }
                    onClick={toggle}
                >
                    {
                        !visible
                            ? (
                                <svg width="30" height="28" viewBox="0 0 30 28" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M0 0.666626H30V3.99996H0V0.666626ZM0 12.3333H30V15.6666H0V12.3333ZM0 24H30V27.3333H0V24Z" fill="black"/>
                                </svg>
                            )
                            : (
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M23.6673 2.68337L21.3173 0.333374L12.0007 9.65004L2.68398 0.333374L0.333984 2.68337L9.65065 12L0.333984 21.3167L2.68398 23.6667L12.0007 14.35L21.3173 23.6667L23.6673 21.3167L14.3507 12L23.6673 2.68337Z" fill="#767676"/>
                                </svg>
                            )
                    }
                </button>
            </nav>
        </header>
    );
}

export default Header;

import "./header.css";
import {Link} from "react-router-dom";
import Search from "../Search/search";
import {useAuth} from "../../context/AuthContext/authContext";
import { useEffect } from 'react';

function Header({ visible ,onMenuClick }) {
    const { auth, setAuth } = useAuth();

    useEffect(() => {
        setAuth(true);
    }, [auth, setAuth]);

    return (
        <header className={'header'}>
            <div className={'header--logo'}>
                <img src="/pictures/svg/header-logo.svg" alt={'Logo'} />
                <img
                    src="/pictures/svg/header-logo-text.svg"
                    alt={'Logo text'}
                    className={'header--logo__disposal'}
                />
            </div>
            <nav className={'nav-panel'}>
                <div className={'nav-panel--set nav-panel--set__disposal'}>
                    <Link to={'#TODO'} className={'nav-panel--link'}>
                        <p>Про нас</p>
                    </Link>
                    <Link to={'#TODO'} className={'nav-panel--link'}>
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
                        <Link to={'#TODO'} className={'nav-panel--link'}>
                            <p>Увійти</p>
                        </Link>
                        <button
                            className={
                                'button button__primary-padding button__primary-color'
                            }
                        >
                            Зареєструватися
                        </button>
                    </div>
                )}
                <button
                    className={
                        'button button__transparent-color nav-panel--menu-btn'
                    }
                    onClick={onMenuClick}
                >
                    <img
                        src={
                            !visible
                                ? '/pictures/svg/menu-open-btn.svg'
                                : '/pictures/svg/menu-close-btn.svg'
                        }
                        alt={'Menu open'}
                    />
                </button>
            </nav>
        </header>
    );
}

export default Header;

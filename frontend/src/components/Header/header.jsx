import "./header.css";
import { Link, useNavigate } from 'react-router-dom';
import Search from "../Search/search";
import {useAuthContext} from "../../provider/AuthProvider/authProvider";
import PropTypes from 'prop-types';
import Button from '../Button/button';
import { useState } from 'react';

/**
 * Header component
 * @param show - function to show the header
 * @param hide - function to hide the header
 * @param toggle - function to toggle the header visibility
 * @param visible - boolean indicating if the header is visible
 * @returns {JSX.Element}
 */
function Header({ show, hide, toggle, visible }) {
    const { logout } = useAuthContext();
    const navigate = useNavigate();
    const { user } = useAuthContext();

    const [loading, setLoading] = useState(false);
    const doLogout = async () => {
        setLoading(true);
        try { await logout(); navigate('/'); }
        finally { setLoading(false); }
    }

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
                    <Link
                        to={'/who-we-are'}
                        className={'link__underline nav-panel--link'}
                    >
                        <p>Про нас</p>
                    </Link>
                    <Link
                        to={'/companies'}
                        className={'link__underline nav-panel--link'}
                    >
                        <p>Підприємства та сектори</p>
                    </Link>
                    <Search className={'nav-panel--search'} />
                </div>
                {(user && user.isAuthorized) ? (
                    <div className={'nav-panel--set dropdown'}>
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
                        <div className={'dropdown-content nav-panel__dropdown--top'}>
                            {user.id &&
                                <Link
                                    to={`/profile/${user.id}`}
                                    className={'dropdown-content__link'}
                                >
                                    Перейти
                                </Link>
                            }
                            {user.id &&
                                <Link
                                    to={`/profile/${user.id}/edit`}
                                    className={'dropdown-content__link'}
                                >
                                    Редагувати
                                </Link>
                            }
                            <button
                                className={'dropdown-content__btn text-danger'}
                                onClick={doLogout}
                                disabled={loading}
                            >
                                Вийти
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className={'nav-panel--set'}>
                        <Link
                            to={'/auth/login'}
                            className={'link__underline nav-panel--link'}
                        >
                            <p>Увійти</p>
                        </Link>
                        <Button
                            className={'button__padding'}
                            onClick={() => navigate('/auth/register')}
                        >
                            Зареєструватися
                        </Button>
                    </div>
                )}
                <Button
                    variant="outline"
                    className={'nav-panel--menu-btn'}
                    onClick={toggle}
                >
                    {!visible ? (
                        <svg
                            width="30"
                            height="28"
                            viewBox="0 0 30 28"
                            fill="none"
                            xmlns="http://www.w3.org/2000/svg"
                        >
                            <path
                                d="M0 0.666626H30V3.99996H0V0.666626ZM0 12.3333H30V15.6666H0V12.3333ZM0 24H30V27.3333H0V24Z"
                                fill="black"
                            />
                        </svg>
                    ) : (
                        <svg
                            width="24"
                            height="24"
                            viewBox="0 0 24 24"
                            fill="none"
                            xmlns="http://www.w3.org/2000/svg"
                        >
                            <path
                                d="M23.6673 2.68337L21.3173 0.333374L12.0007 9.65004L2.68398 0.333374L0.333984 2.68337L9.65065 12L0.333984 21.3167L2.68398 23.6667L12.0007 14.35L21.3173 23.6667L23.6673 21.3167L14.3507 12L23.6673 2.68337Z"
                                fill="#767676"
                            />
                        </svg>
                    )}
                </Button>
            </nav>
        </header>
    );
}

/**
 * PropTypes for Header component
 * @property {function} show - Function to show the header
 * @property {function} hide - Function to hide the header
 * @property {function} toggle - Function to toggle the header visibility
 * @property {boolean} visible - Boolean indicating if the header is visible
 */
Header.porpTypes = {
    show: PropTypes.func.isRequired,
    hide: PropTypes.func.isRequired,
    toggle: PropTypes.func.isRequired,
    visible: PropTypes.bool.isRequired
};

export default Header;

import './footer.css';
import { Link } from 'react-router-dom';

/**
 * Footer component that renders the footer section of the application.
 * It includes contact information, a link tree for navigation,
 * and developer contact information.
 * @returns {JSX.Element}
 */
function Footer() {
    return (
        <footer className={'footer'}>
            <section className={'contacts'}>
                <div className={'contacts--logo'}>
                    <img
                        src="/pictures/svg/footer-logo.svg"
                        alt="Footer Logo"
                    />
                </div>
                <div className={'contacts--content'}>
                    <div className={'contacts--info'}>
                        <p>Львівська Політехніка</p>
                        <p>вул. Степана Бандери 12, Львів</p>
                    </div>
                    <div className={'contacts--links'}>
                        <a href={'mailto:qwerty@gmail.com'}
                            className={'contacts--link'}
                        >
                            <img src="/pictures/svg/mail.svg" alt="Mail" />
                            <p>qwerty@gmail.com</p>
                        </a>
                        <a href={'tel:+380502342323'}
                            className={'contacts--link'}
                        >
                            <img src="/pictures/svg/phone.svg" alt="Phone" />
                            <p>+38 050 234 23 23</p>
                        </a>
                    </div>
                </div>
            </section>
            <section className={'link-tree'}>
                <div className={'branch-list'}>
                    <div className={'branch-list--branch'}>
                        <h2 className={'branch-list--title'}>Підприємства</h2>
                        <div className={'branch-list--link-list'}>
                            <Link to={'/companies'} className={'branch-list--item'}>
                                <p>Компанії</p>
                            </Link>
                            <Link to={'/startups'} className={'branch-list--item'}>
                                <p>Стартапи</p>
                            </Link>
                        </div>
                    </div>
                    <div className={'branch-list--branch'}>
                        <h2 className={'branch-list--title'}>Сектори</h2>
                        <div className={'branch-list--link-list'}>
                            <Link to={'/manufacturers'} className={'branch-list--item'}>
                                <p>Виробники</p>
                            </Link>
                            <Link to={'/importers'} className={'branch-list--item'}>
                                <p>Імпортери</p>
                            </Link>
                            <Link to={'/retails'} className={'branch-list--item'}>
                                <p>Роздрібні мережі</p>
                            </Link>
                            <Link to={'/horeca'} className={'branch-list--item'}>
                                <p>HORECA</p>
                            </Link>
                            <Link to={'/other-services'} className={'branch-list--item'}>
                                <p>Інші послуги</p>
                            </Link>
                        </div>
                    </div>
                </div>
            </section>
            <hr className={'footer--hr'} />
            <section className={'dev-contact'}>
                <div>
                    <img
                        src="/pictures/svg/opentech-logo.svg"
                        alt="Dev-Company Logo"
                    />
                </div>
                <div className={'dev-contact--container'}>
                    <div className={'dev-contact--list'}>
                        <Link to={'/privacy-policy'}>
                            <p>Політика конфіденційності</p>
                        </Link>
                        <Link to={'/terms-of-use'}>
                            <p>Умови користування</p>
                        </Link>
                        <Link to={'/feedback'}>
                            <p>Зворотній звʼязок</p>
                        </Link>
                    </div>
                    <p className={'dev-contact--copyright'}>
                        Copyright 2023 Forum. All rights reserved.
                    </p>
                </div>
            </section>
        </footer>
    );
}

export default Footer;

import './sidebar.css';
import Dimmer from '../Dimmer/dimmer';
import Search from '../Search/search';
import { Link } from 'react-router-dom';
import { useEffect } from 'react';
import PropTypes from 'prop-types';

/**
 * Sidebar component
 * @param show - function to show the sidebar
 * @param hide - function to hide the sidebar
 * @param toggle - function to toggle the sidebar visibility
 * @param visible - boolean indicating if the sidebar is visible
 * @param children - children elements to be rendered inside the sidebar
 * @returns {JSX.Element}
 */
function Sidebar({ show, hide, toggle, visible, children }) {
    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.key === 'Escape' && visible) {
            }
        }

        if (visible) {
            window.addEventListener("keydown", handleKeyDown);
        }

        return () => {
            window.removeEventListener("keydown", handleKeyDown);
        };
    }, [visible, hide]);

    return (
        <div className={"sidebar-wrapper"}>
            <Dimmer isActive={visible} hideDimmer={hide}>
                <div
                    role="dialog"
                    aria-modal="true"
                    aria-hidden={!visible}
                    aria-labelledby="sidebar-title"
                    onClick={(e) => e.stopPropagation()}
                >
                    <hr className={"sidebar--hr"} />
                    <div className={"sidebar--menu"}>
                        <h2 id="sidebar-title" className="visually-hidden">Меню сайдбара</h2>
                        <Search width={'100%'} />
                        <Link to={"/who-we-are"} className={"sidebar--link"}>
                            <p>Про нас</p>
                        </Link>
                        <Link to={"/companies"} className={"sidebar--link"}>
                            <p>Підприємства та сектори</p>
                        </Link>
                    </div>
                </div>
            </Dimmer>
            {children}
        </div>
    );
}

/**
 * PropTypes for Header component
 * @property {function} show - Function to show the header
 * @property {function} hide - Function to hide the header
 * @property {function} toggle - Function to toggle the header visibility
 * @property {boolean} visible - Boolean indicating if the header is visible
 */
Sidebar.porpTypes = {
    show: PropTypes.func.isRequired,
    hide: PropTypes.func.isRequired,
    toggle: PropTypes.func.isRequired,
    visible: PropTypes.bool.isRequired
};

export default Sidebar;

import "./panel.css";
import PropTypes from 'prop-types';
import clsx from 'clsx';
import { Link } from 'react-router-dom';
import React from 'react';

/**
 * Panel component to wrap content with a styled container.
 * It can be used to create sections with titles, bodies, and navigation.
 * @param children - The content to be displayed inside the panel.
 * @returns {JSX.Element}
 */
function PanelTitle({ children }) {
    return <h2 className={'panel--title'}>{ children }</h2>;
}

PanelTitle.propTypes = {
    children: PropTypes.node.isRequired
}

/**
 * PanelBody component to wrap the main content of the panel.
 * It includes horizontal rules before and after the content for visual separation.
 * It is typically used to display the main body of the panel.
 * @param children - The content to be displayed inside the panel body.
 * @returns {JSX.Element}
 */
function PanelBody({ children }) {
    return (
        <>
            <hr className={'panel--hr'} />
            <div className={'panel--content'}>
                { children }
            </div>
            <hr className={'panel--hr'} />
        </>
    );
}

PanelBody.propTypes = {
    children: PropTypes.node.isRequired
}

/**
 * PanelBodyTitle component to display a title with a star indicator and additional text.
 * It is typically used to highlight important titles within the panel body.
 * The star indicates that the title is required or important.
 * It accepts a title and children for additional text.
 * @param title - The title text to be displayed, typically indicating a required field.
 * @param children - Additional text to be displayed below the title, providing more context or instructions.
 * @param className - Additional CSS class names to apply to the title container.
 * @param required - A boolean indicating if the title is required (typically used to show a star).
 * @returns {JSX.Element}
 */
function PanelBodyTitle({ title, children, className = '', required = true }) {
    return (
        <div className={clsx('content--text-container', className)}>
            {required && <span className={'content--text content--text__starred content--text__margin'}>*</span>}
            <div>
                {title && <span className={'content--text'}>{ title }</span>}
                {children && <p className={'content--subtext'}>{ children }</p>}
            </div>
        </div>
    );
}

PanelBodyTitle.propTypes = {
    required: PropTypes.bool,
    title: PropTypes.string,
    children: PropTypes.node,
    className: PropTypes.string
}

/**
 * PanelBodyBottomLink is used in pair with input field.
 *
 * @example
 * <Input>Password</Input>
 * <PanelBodyBottomLink
 *     linkText="Забули пароль?"
 *     to="/auth/forgot"
 * />
 *
 * @component
 *
 * @param linkText - Text that will be displayed
 * @param to - Link URL
 * @param className - Additional style settings
 * @returns {JSX.Element}
 */
const PanelBodyBottomLink = React.memo(function PanelBodyBottomLink({ linkText, to, className }) {
    return (
        <Link to={to} className={clsx('text-underline', 'text-bold', 'content__link-container', className)}>
            { linkText }
        </Link>
    );
});

PanelBodyBottomLink.propTypes = {
    linkText: PropTypes.string.isRequired,
    to: PropTypes.string.isRequired,
    className: PropTypes.string
}

/**
 * PanelNavigation component to wrap navigation elements within the panel.
 * It is typically used to display navigation links or buttons related to the panel's content.
 * @param children - The navigation elements to be displayed inside the panel navigation.
 * @returns {JSX.Element}
 */
function PanelNavigation({ children }) {
    return <div className={"panel--navigation"}>{ children }</div>;
}

PanelNavigation.propTypes = {
    children: PropTypes.node.isRequired
}

/**
 * Panel component to create a styled container for the panel.
 * It accepts a className prop for additional styling and wraps the children content.
 * This component is typically used to create a consistent layout for panels.
 * @param className - Additional CSS class names to apply to the panel.
 * @param children - The content to be displayed inside the panel.
 * @returns {JSX.Element}
 */
function Panel({ className, children }) {
    return <div className={clsx('panel', 'panel__margin', className)}>{children}</div>;
}

export { PanelTitle, PanelBody, PanelBodyTitle, PanelBodyBottomLink, PanelNavigation };
export default Panel;

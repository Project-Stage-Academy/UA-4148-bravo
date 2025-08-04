import "./panel.css";
import PropTypes from 'prop-types';

/**
 * Panel component to wrap content with a styled container.
 * It can be used to create sections with titles, bodies, and navigation.
 * @param children - The content to be displayed inside the panel.
 * @returns {JSX.Element}
 */
function PanelTitle({ children }) {
    return <h2 className={'panel--title'}>{ children }</h2>;
}

/**
 * PanelTitle component to display the title of the panel.
 * It is typically used to provide a heading for the panel content.
 * @param children - The title text to be displayed inside the panel title.
 */
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

/**
 * PanelBody component to display the main content of the panel.
 * It is typically used to provide a structured layout for the panel's body content.
 * @param children - The content to be displayed inside the panel body.
 */
PanelBody.propTypes = {
    children: PropTypes.node.isRequired
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

/**
 * PanelNavigation component to display navigation elements within the panel.
 * It is typically used to provide navigation options related to the panel's content.
 * @param children - The navigation elements to be displayed inside the panel navigation.
 */
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
    return <div className={`panel panel__margin ${className}`}>{children}</div>;
}

export { PanelTitle, PanelBody, PanelNavigation };
export default Panel;

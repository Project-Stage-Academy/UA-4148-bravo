import './dimmer.css';

/**
 * Dimmer component to overlay content with a semi-transparent background.
 * It can be used to block user interaction with the underlying content.
 * The dimmer can be activated or deactivated based on the `isActive` prop.
 * When active, it displays a semi-transparent overlay that covers the entire viewport.
 * Clicking on the overlay will trigger the `hideDimmer` function to deactivate it.
 * @param isActive - boolean indicating if the dimmer is active
 * @param hideDimmer - function to call when the dimmer is clicked to hide it
 * @param children - React elements to be displayed on top of the dimmer
 * @returns {JSX.Element}
 */
function Dimmer({ isActive, hideDimmer, children }) {
    return <>
        {isActive && <div className="dimmer-overlay" onClick={hideDimmer}>
            { children }
        </div>}
    </>;
}

export default Dimmer;

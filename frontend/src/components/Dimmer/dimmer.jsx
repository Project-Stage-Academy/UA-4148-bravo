import './dimmer.css';

function Dimmer({ isActive, hideDimmer, children }) {
    return <>
        {isActive && <div className="dimmer-overlay" onClick={hideDimmer}>
            { children }
        </div>}
    </>;
}

export default Dimmer;

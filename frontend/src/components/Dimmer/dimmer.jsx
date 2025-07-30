import './dimmer.css';

function Dimmer({ isActive ,children }) {
    return <>
        {isActive && <div className="dimmer-overlay">
            { children }
        </div>}
    </>;
}

export default Dimmer;

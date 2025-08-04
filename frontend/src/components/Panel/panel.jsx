import "./panel.css";

export function PanelTitle({ children }) {
    return <h2 className={'panel--title'}>{ children }</h2>;
}

export function PanelBody({ children }) {
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

export function PanelNavigation({ children }) {
    return <div className={"panel--navigation"}>{ children }</div>;
}

function Panel({ className, children }) {
    return (
        <div className={`panel panel__margin ${className}`}>
            { children }
        </div>
    );
}

export default Panel;

import './sidebar.css';
import { forwardRef, useImperativeHandle, useState } from 'react';
import Dimmer from '../Dimmer/dimmer';
import Search from '../Search/search';
import { Link } from 'react-router-dom';

const Sidebar = forwardRef(function Sidebar({ children }, ref) {
    const [dimmerActive, setDimmerActive] = useState(false);

    useImperativeHandle(ref, () => ({
        show: () => setDimmerActive(true),
        hide: () => setDimmerActive(false),
        toggle: () => setDimmerActive(v => !v),
        dimmerActive,
    }));

    return (
        <div className={"sidebar-wrapper"}>
            <Dimmer isActive={dimmerActive}>
                <hr className={"sidebar--hr"}/>
                <div className={"sidebar--menu"}>
                    <Search width={'100%'} />
                    <Link to={"/who-we-are"} className={"sidebar--link"}>
                        <p>Про нас</p>
                    </Link>
                    <Link to={"/companies"} className={"sidebar--link"}>
                        <p>Підприємства та сектори</p>
                    </Link>
                </div>
            </Dimmer>
            {children}
        </div>
    );
});

export default Sidebar;

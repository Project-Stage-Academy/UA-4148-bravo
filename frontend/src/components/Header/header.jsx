import "./header.css";
import {Link} from "react-router-dom";
import Search from "../Search/search";
import {useAuth} from "../../context/AuthContext/authContext";

function Header() {
    const { auth, setAuth } = useAuth();
    setAuth(false);

    return (
        <header className={"header"}>
            <img src="./pictures/svg/header-logo.svg" alt={"Logo"}/>
            <nav className={"nav-panel"}>
                <Link to={"#TODO"} className={"nav-panel--link"}>
                    <p>Про нас</p>
                </Link>
                <Link to={"#TODO"} className={"nav-panel--link"}>
                    <p>Підприємства та сектори</p>
                </Link>
                <Search width={"225px"}/>
                {auth ? (
                    <>
                        <Link to={"#TODO"} className={"nav-panel--link"}>
                            <img src="./pictures/svg/avatar.svg" alt={"User avatar"}/>
                            <p>Мій профіль</p>
                        </Link>
                    </>
                ) : (
                    <>
                        <Link to={"#TODO"} className={"nav-panel--link"}>
                            <p>Увійти</p>
                        </Link>
                        <button className={"button button__primary-color"}>Зареєструватися</button>
                    </>
                )}
            </nav>
        </header>
    );
}

export default Header;

import './notFound.css';
import { useNavigate } from 'react-router-dom';
import Button from '../../components/Button/button';

/**
 * NotFound component renders a 404 Not Found page.
 * It provides a message indicating that the requested page could not be found
 * and includes a button to navigate back to the home page.
 * @returns {JSX.Element}
 */
function NotFound() {
    const navigate = useNavigate();
    const returnToHomePage = () => {
        navigate('/');
    };

    return (
        <div className={'not-found'}>
            <section className={'not-found--container'}>
                <h1 className={"not-found--title"}>404</h1>
                <div className={"not-found--content"}>
                    <h2 className={"not-found--subtitle"}>Щось пішло не так</h2>
                    <p className={"not-found--description"}>
                        Схоже, це неправильна адреса, ця сторінка видалена,
                        перейменована або тимчасово недоступна.
                    </p>
                    <div>
                        <Button className={"button__padding"}
                                onClick={returnToHomePage}>
                            Повернутися на головну
                        </Button>
                    </div>
                </div>
            </section>
        </div>
    );
}

export default NotFound;

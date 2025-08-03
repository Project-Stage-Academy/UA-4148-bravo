import './notFound.css';
import { useNavigate } from 'react-router-dom';
import Button from '../../components/Button/button';

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

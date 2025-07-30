import './notFound.css';
import { useNavigate } from 'react-router-dom';

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
                        <button
                            className={'button button__primary-padding button__primary-color'}
                            onClick={returnToHomePage}
                        >
                            <span>Повернутися на головну</span>
                        </button>
                    </div>
                </div>
            </section>
        </div>
    );
}

export default NotFound;

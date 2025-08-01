import "./registration.css";
import { useNavigate } from 'react-router-dom';

function RegistrationDone() {
    const navigate = useNavigate();

    function handleSubmit() {
        navigate("/");
    }

    return (
        <div className={'panel panel__margin'}>
            <h2 className={'panel--title'}>Реєстрація завершена!</h2>
            <hr className={'panel--hr'} />
            <div className={'panel--content'}>
                <div>
                    <p className={"panel--font-size"}>
                        Ви успішно підтвердили вказану електронну адресу.
                    </p>
                </div>
            </div>
            <hr className={'panel--hr'} />
            <div className={"panel--navigation"}>
                <button
                    onClick={handleSubmit}
                    className={
                        'button button__padding button__primary-color panel--button'
                    }
                >
                    Повернутися до входу
                </button>
            </div>
        </div>
    );
}

export default RegistrationDone;

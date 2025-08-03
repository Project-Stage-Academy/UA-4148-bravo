import "./registrationError.css";
import { useNavigate } from 'react-router-dom';

function RegistrationError() {
    const navigate = useNavigate();

    function handleSubmit() {
        navigate("/");
    }

    return (
        <div className={'panel panel__margin panel__margin-large'}>
            <h2 className={'panel--title'}>Помилка активації</h2>
            <hr className={'panel--hr'} />
            <div className={'panel--content'}>
                <div>
                    <p className={"panel--font-size"}>
                        Під час активації сталася помилка. Спробуйте ще раз або звʼяжіться з підтримкою.
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

export default RegistrationError;

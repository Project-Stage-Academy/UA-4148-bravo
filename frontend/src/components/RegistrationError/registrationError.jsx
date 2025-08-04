import "./registrationError.css";
import { useNavigate } from 'react-router-dom';
import Button from '../Button/button';

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
                <Button
                    onClick={handleSubmit}
                    className={'button__padding panel--button'}
                >
                    Повернутися до входу
                </Button>
            </div>
        </div>
    );
}

export default RegistrationError;

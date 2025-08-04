import "./registration.css";
import { useNavigate } from 'react-router-dom';
import Button from '../Button/button';

function RegistrationDone() {
    const navigate = useNavigate();

    function handleSubmit() {
        navigate("/");
    }

    return (
        <div className={'panel panel__margin panel__margin-large'}>
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

export default RegistrationDone;

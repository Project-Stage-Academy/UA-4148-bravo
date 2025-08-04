import "./registrationConfirmation.css";
import { useNavigate } from 'react-router-dom';
import Button from '../Button/button';

function RegistrationConfirmation() {
    const navigate = useNavigate();

    function handleReturn() {
        navigate("/");
    }

    function sendEmailAgain() {
        navigate("/auth/register/re-confirm");
    }

    return (
        <div className={'panel panel__margin panel__margin-large'}>
            <h2 className={'panel--title'}>Реєстрація  майже завершена</h2>
            <hr className={'panel--hr'} />
            <div className={'panel--content'}>
                <div>
                    <p className={"panel--font-size"}>
                        На зазначену вами електронну пошту відправлено листа.
                    </p>
                    <p className={"panel--font-size"}>Будь ласка, перейдіть за посиланням з листа для підтвердження вказаної електронної адреси.</p>
                </div>
                <div>
                    <span className={"panel--font-size"}>
                        Не отримали листа?
                    </span>
                    <Button variant='outline' className={'panel--font-size text-underline text-bold'} onClick={sendEmailAgain}>
                        Надіслати ще раз
                    </Button>
                </div>
            </div>
            <hr className={'panel--hr'} />
            <div className={"panel--navigation"}>
                <Button
                    onClick={handleReturn}
                    className={'button__padding panel--button'}
                >
                    Повернутися до входу
                </Button>
            </div>
        </div>
    );
}

export default RegistrationConfirmation;

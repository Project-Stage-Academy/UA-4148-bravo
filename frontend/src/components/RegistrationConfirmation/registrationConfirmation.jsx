import "./registrationConfirmation.css";
import { useNavigate } from 'react-router-dom';

function RegistrationConfirmation() {
    const navigate = useNavigate();

    function handleSubmit() {
        navigate("/");
    }

    function sendEmailAgain() {
        navigate("/auth/register/re-confirmation");
    }

    return (
        <div className={'panel panel__margin'}>
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
                    <button className={'button button__transparent-color panel--font-size text-underline text-bold'} onClick={sendEmailAgain}>
                        Надіслати ще раз
                    </button>
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

export default RegistrationConfirmation;

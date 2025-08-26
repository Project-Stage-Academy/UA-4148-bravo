import "./registrationConfirmation.css";
import { useNavigate } from 'react-router-dom';
import Button from '../../components/Button/button';
import Panel, { PanelBody, PanelNavigation, PanelTitle } from '../../components/Panel/panel';

/**
 * Registration page that informs the user to
 * check their email to confirm their account
 *
 * @component
 *
 * @returns {JSX.Element}
 */
function RegistrationConfirmation() {
    // This component handles user registration
    const navigate = useNavigate();

    // Function to handle the return button click
    function handleReturn() {
        navigate("/");
    }

    // Function to handle the resend email button click
    function sendEmailAgain() {
        navigate("/auth/register/re-confirm");
    }

    return (
        <Panel className={"panel__margin-large"}
               aria-labelledby="registrationConfirmation-title"
        >
            <PanelTitle id="registrationConfirmation-title"
                        aria-describedby="registrationConfirmation-help1 registrationConfirmation-help2"
            >
                Реєстрація майже завершена
            </PanelTitle>
            <PanelBody>
                <div>
                    <p id="registrationConfirmation-help1"
                       className={"panel--font-size"}
                    >
                        На зазначену вами електронну пошту відправлено листа.
                    </p>
                    <p id="registrationConfirmation-help2"
                       className={"panel--font-size"}
                    >
                        Будь ласка, перейдіть за посиланням з листа
                        для підтвердження вказаної електронної адреси.
                    </p>
                </div>
                <div>
                    <span className={"panel--font-size"}>
                        Не отримали листа?
                    </span>
                    <Button variant='outline'
                            className={'panel--font-size text-underline text-bold'}
                            onClick={sendEmailAgain}
                    >
                        Надіслати ще раз
                    </Button>
                </div>
            </PanelBody>
            <PanelNavigation>
                <Button
                    onClick={handleReturn}
                    className={'button__padding panel--button'}
                    type="submit"
                >
                    Повернутися до входу
                </Button>
            </PanelNavigation>
        </Panel>
    );
}

export default RegistrationConfirmation;

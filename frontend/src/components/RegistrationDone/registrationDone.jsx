import "./registration.css";
import { useNavigate } from 'react-router-dom';
import Button from '../Button/button';
import Panel, { PanelBody, PanelNavigation, PanelTitle } from '../Panel/panel';

function RegistrationDone() {
    // This component handles user registration
    const navigate = useNavigate();

    // Function to handle the submission of the registration form
    function handleSubmit() {
        navigate("/");
    }

    return (
        <Panel className={"panel__margin-large"}>
            <PanelTitle>Реєстрація завершена!</PanelTitle>
            <PanelBody>
                <div>
                    <p className={"panel--font-size"}>
                        Ви успішно підтвердили вказану електронну адресу.
                    </p>
                </div>
            </PanelBody>
            <PanelNavigation>
                <Button
                    onClick={handleSubmit}
                    className={'button__padding panel--button'}
                >
                    Повернутися до входу
                </Button>
            </PanelNavigation>
        </Panel>
    );
}

export default RegistrationDone;

import "./registrationUserConfirmed.css";
import { useNavigate } from 'react-router-dom';
import Button from '../../components/Button/button';
import Panel, { PanelBody, PanelNavigation, PanelTitle } from '../../components/Panel/panel';

function RegistrationUserConfirmed() {
    // This component handles user registration
    const navigate = useNavigate();

    // Function to handle the submission of the registration form
    function handleSubmit() {
        navigate("/auth/register/user-represent");
    }

    return (
        <Panel className={"panel__margin-large"}>
            <PanelTitle>Залишилось декілька кроків</PanelTitle>
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
                    Продовжити реєстрацію
                </Button>
            </PanelNavigation>
        </Panel>
    );
}

export default RegistrationUserConfirmed;

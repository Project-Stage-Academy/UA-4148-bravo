import "./registrationError.css";
import { useNavigate } from 'react-router-dom';
import Button from '../../components/Button/button';
import Panel, { PanelBody, PanelNavigation, PanelTitle } from '../../components/Panel/panel';

function RegistrationError() {
    // This component handles user registration
    const navigate = useNavigate();

    // Function to handle form submission
    function handleSubmit() {
        navigate("/");
    }

    return (
        <Panel className={"panel__margin-large"}>
            <PanelTitle>Помилка активації</PanelTitle>
            <PanelBody>
                <div>
                    <p className={"panel--font-size"}>
                        Під час активації сталася помилка. Спробуйте ще раз або звʼяжіться з підтримкою.
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

export default RegistrationError;

import "./registrationError.css";
import { useNavigate } from 'react-router-dom';
import Button from '../Button/button';
import Panel, { PanelBody, PanelNavigation, PanelTitle } from '../Panel/panel';

function RegistrationError() {
    const navigate = useNavigate();

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

import { useNavigate } from 'react-router-dom';
import Panel, {
    PanelBody,
    PanelNavigation,
    PanelTitle,
} from '../../components/Panel/panel';
import Button from '../../components/Button/button';

/**
 * Registration page that informs
 * the user that registration is complete
 *
 * @component
 *
 * @returns {JSX.Element}
 */
function RegistrationCompleted() {
    // This component handles user registration
    const navigate = useNavigate();

    // Function to handle the submission
    function handleSubmit() {
        navigate("/");
    }

    return (
        <Panel className={"panel__margin-large"}>
            <PanelTitle>Реєстрація завершена!</PanelTitle>
            <PanelBody>
                <div>
                    <p className={"panel--font-size"}>
                        Ви успішно завершили реєстрацію
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

export default RegistrationCompleted;

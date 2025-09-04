import "./registrationUserConfirmed.css";
import { useNavigate } from 'react-router-dom';
import Button from '../../components/Button/button';
import Panel, { PanelBody, PanelNavigation, PanelTitle } from '../../components/Panel/panel';

/**
 * A registration page that indicates that the
 * user has confirmed their email address
 *
 * @component
 *
 * @returns {JSX.Element}
 */
function RegistrationUserConfirmed() {
    // This component handles user registration
    const navigate = useNavigate();

    // Function to handle the submission of the registration form
    function handleSubmit() {
        navigate("/auth/login");
    }

    return (
        <Panel aria-labelledby="registrationUserConfirmed-title"
               className={"panel__margin-large"}
        >
            <PanelTitle id="registrationUserConfirmed-title"
                        aria-describedby="registrationUserConfirmed-help"
            >
                Залишилось декілька кроків
            </PanelTitle>
            <PanelBody>
                <div>
                    <p id="registrationUserConfirmed-help"
                       className={"panel--font-size"}
                    >
                        Ви успішно підтвердили вказану електронну адресу.
                    </p>
                </div>
            </PanelBody>
            <PanelNavigation>
                <Button
                    onClick={handleSubmit}
                    className={'button__padding panel--button'}
                    type="submit"
                >
                    Увійти в профіль
                </Button>
            </PanelNavigation>
        </Panel>
    );
}

export default RegistrationUserConfirmed;

import './registrationUserRepresent.css';
import { useNavigate } from 'react-router-dom';
import Panel, { PanelBody, PanelNavigation, PanelTitle } from '../../components/Panel/panel';
import Button from '../../components/Button/button';

/**
 * Registration page that asks the user to select
 * who they represent: Company or Startup project
 *
 * @component
 *
 * @returns {JSX.Element}
 */
function RegistrationUserRepresent() {
    // This component handles user registration
    const navigate = useNavigate();

    // The user selects the option that he represents the company
    function handleSubmitCompany() {
        navigate("/auth/register/entity-represent");
    }

    // The user selects the option that he represents the startup
    function handleSubmitStartup() {
        navigate("/auth/register/entity-represent");
    }

    return (
        <Panel className={"panel__margin-large"}>
            <PanelTitle>Залишилось декілька кроків</PanelTitle>
            <PanelBody>
                <div>
                    <p className={"panel--font-size"}>
                        Кого ви представляєте?
                    </p>
                </div>
            </PanelBody>
            <PanelNavigation>
                <Button
                    onClick={handleSubmitCompany}
                    variant={'secondary'}
                    className={'button__padding panel--button registration-user-represent__button--flex'}
                >
                    Компанія
                </Button>
                <Button
                    onClick={handleSubmitStartup}
                    variant={'secondary'}
                    className={'button__padding panel--button registration-user-represent__button--flex'}
                >
                    Стартап проєкт
                </Button>
            </PanelNavigation>
        </Panel>
    );
}

export default RegistrationUserRepresent;

import './registrationEntityRepresent.css';
import { useNavigate } from 'react-router-dom';
import Panel, { PanelBody, PanelNavigation, PanelTitle } from '../../components/Panel/panel';
import Button from '../../components/Button/button';

/**
 * Registration page that asks the user to select
 * who they represent: Individual entrepreneur or Legal entity
 *
 * @component
 *
 * @returns {JSX.Element}
 */
function RegistrationEntityRepresent() {
    // This component handles user registration
    const navigate = useNavigate();

    // The user selects the option that he represents the individual entrepreneur
    function handleSubmitIndividual() {
        navigate("/auth/register/completed");
    }

    // The user selects the option that he represents the legal entity
    function handleSubmitLegal() {
        navigate("/auth/register/completed");
    }

    return (
        <Panel className={"panel__margin-large"}>
            <PanelTitle>Останній крок</PanelTitle>
            <PanelBody>
                <div>
                    <p className={"panel--font-size"}>
                        Який суб’єкт господарювання ви представляєте?
                    </p>
                </div>
            </PanelBody>
            <PanelNavigation>
                <Button
                    onClick={handleSubmitIndividual}
                    variant={'secondary'}
                    className={'button__padding panel--button registration-entity-represent__button--flex'}
                >
                    Фізична особа-підприємець
                </Button>
                <Button
                    onClick={handleSubmitLegal}
                    variant={'secondary'}
                    className={'button__padding panel--button registration-entity-represent__button--flex'}
                >
                    Юридична особа
                </Button>
            </PanelNavigation>
        </Panel>
    );
}

export default RegistrationEntityRepresent;

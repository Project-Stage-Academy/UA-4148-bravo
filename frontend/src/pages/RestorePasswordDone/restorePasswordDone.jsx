import "./restorePasswordDone.css";
import Panel, { PanelBody, PanelNavigation, PanelTitle } from '../../components/Panel/panel';
import Button from '../../components/Button/button';
import { useNavigate } from 'react-router-dom';

/**
 * RestorePasswordDone component displays a confirmation message
 * after the user has successfully restored their password.
 * It provides a button to navigate back to the login page.
 * @returns {JSX.Element}
 */
function RestorePasswordDone() {
    const navigate = useNavigate();

    const handleSubmit = () => {
        navigate('/');
    };

    return (
        <Panel>
            <PanelTitle>Пароль збережено</PanelTitle>
            <PanelBody>
                <p>Ваш новий пароль успішно збережено</p>
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

export default RestorePasswordDone;

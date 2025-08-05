import "./restorePasswordDone.css";
import Panel, { PanelBody, PanelNavigation, PanelTitle } from '../../components/Panel/panel';
import Button from '../../components/Button/button';
import { useNavigate } from 'react-router-dom';

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

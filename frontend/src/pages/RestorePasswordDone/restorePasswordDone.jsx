import "./restorePasswordDone.css";
import Panel, {
    PanelBody,
    PanelNavigation,
    PanelTitle,
} from '../../components/Panel/panel';
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

    return (
        <>
            <Panel aria-labelledby="restore-password-form-title">
                <PanelTitle id="restore-password-form-title"
                            aria-describedby="restore-password-help1"
                >
                    Пароль успішно змінено
                </PanelTitle>
                <PanelBody>
                    <div>
                        <p id="restore-password-help1"
                           className={'panel--font-size'}
                        >
                            Ваш пароль було успішно змінено. Тепер ви можете
                            увійти, використовуючи свій новий пароль.
                        </p>
                    </div>
                </PanelBody>
                <PanelNavigation>
                    <Button
                        type="button"
                        onClick={() => navigate('/')}
                        className={'button__padding panel--button'}
                    >
                        Повернутися до входу
                    </Button>
                </PanelNavigation>
            </Panel>
        </>
    );
}

export default RestorePasswordDone;

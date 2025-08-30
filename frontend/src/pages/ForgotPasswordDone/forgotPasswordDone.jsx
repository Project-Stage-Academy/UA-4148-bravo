import './forgotPasswordDone.css';
import Panel, { PanelBody, PanelNavigation, PanelTitle } from '../../components/Panel/panel';
import Button from '../../components/Button/button';
import { useNavigate } from 'react-router-dom';

function ForgotPasswordDone() {
    const navigate = useNavigate();

    return (
        <>
            <Panel aria-labelledby="forgot-password-form-title">
                <PanelTitle id="forgot-password-form-title"
                            aria-describedby="forgot-password-help1"
                >
                    Відновлення паролю майже завершено
                </PanelTitle>
                <PanelBody>
                    <div>
                        <p id="forgot-password-help1"
                           className={'panel--font-size'}
                        >
                            На вашу електронну адресу були надіслані інструкції для зміни паролю.
                        </p>
                    </div>
                </PanelBody>
                <PanelNavigation>
                    <Button
                        onClick={() => navigate('/')}
                        className={'button__padding panel--button'}
                        type="submit"
                    >
                        Повернутися до входу
                    </Button>
                </PanelNavigation>
            </Panel>
        </>
    );
}

export default ForgotPasswordDone;

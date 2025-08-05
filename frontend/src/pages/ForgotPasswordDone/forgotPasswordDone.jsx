import './forgotPasswordDone.css';
import Panel, { PanelBody, PanelNavigation, PanelTitle } from '../../components/Panel/panel';
import Button from '../../components/Button/button';
import { useNavigate } from 'react-router-dom';

function ForgotPassword() {
    const navigate = useNavigate();

    return (
        <>
            <Panel>
                <PanelTitle>Відновлення паролю майже завершено</PanelTitle>
                <PanelBody>
                    <div>
                        <p className={'panel--font-size'}>
                            На вашу електронну адресу були надіслані інструкції для зміни паролю.
                        </p>
                    </div>
                </PanelBody>
                <PanelNavigation>
                    <Button
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

export default ForgotPassword;

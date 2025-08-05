import { Link, useNavigate } from 'react-router-dom';
import Panel, { PanelBody, PanelBodyTitle, PanelNavigation, PanelTitle } from '../../components/Panel/panel';
import Button from '../../components/Button/button';
import { useState } from 'react';
import { Validator } from '../../utils/validation/validate';
import { restorePassword } from '../../api';
import HiddenInput from '../../components/HiddenInput/hiddenInput';

/**
 * RestorePassword component handles the user password restoration process.
 * It allows users to set a new password and confirm it.
 * It validates the input and displays any errors that occur during the process.
 * If the password is successfully restored, it navigates to a confirmation page.
 * If there are validation errors or server-side errors, it displays appropriate messages.
 * @returns {JSX.Element}
 */
function RestorePassword() {
    // This component handles user registration
    const navigate = useNavigate();

    // State to hold form data
    const [formData, setFormData] = useState(
        {
            password: "",
            confirmPassword: "",
            unexpected: ""
        });

    // State to hold validation errors
    const [errors, setErrors] = useState({});

    // Function to handle server-side errors
    const handleError = () => {
        setErrors(prev => ({
            ...prev,
            unexpected: Validator.serverSideErrorMessages.unexpected
        }));
    };

    // Function to handle form submission
    const handleSubmit = () => {
        const validationErrors = Validator.validate(
            formData
        );
        setErrors(validationErrors);

        if (Object.values(validationErrors).every(value => value === null)) {
            restorePassword(formData)
                .then(() => navigate('/restore-password/done'))
                .catch(handleError);
        } else {
            console.log('Errors:', validationErrors);
        }
    };

    // Function to handle input changes
    const handleChange = (e) => {
        return Validator.handleChange(
            e,
            formData,
            setFormData,
            setErrors
        );
    };

    return (
        <>
            <Panel>
                <PanelTitle>Відновлення паролю</PanelTitle>
                <PanelBody>
                    <div>
                        <PanelBodyTitle title={'Пароль'} className={'content--text-container__margin'}>
                            Пароль повинен мати 8+ символів, містити принаймні велику, малу літеру (A..Z, a..z) та цифру (0..9).
                        </PanelBodyTitle>
                        <HiddenInput
                            name="password"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={formData.password}
                            onChange={handleChange}
                            className={errors['password'] && 'input__error-border-color'}
                        />
                        { errors['password'] && <p className={"panel--danger-text"}>{ errors['password'] }</p> }
                    </div>
                    <div>
                        <PanelBodyTitle title={'Повторіть пароль'} className={'content--text-container__margin'} />
                        <HiddenInput
                            name="confirmPassword"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={formData.confirmPassword}
                            onChange={handleChange}
                            className={errors['confirmPassword'] && 'input__error-border-color'}
                        />
                        { errors['confirmPassword'] && <p className={"panel--danger-text"}>{ errors["confirmPassword"] }</p> }
                    </div>
                    { errors['unexpected'] && <p className={"panel--danger-text"}>{ errors['unexpected'] }</p>}
                </PanelBody>
                <PanelNavigation>
                    <Button
                        onClick={handleSubmit}
                        className={'button__padding panel--button'}
                    >
                        Зберегти пароль
                    </Button>
                </PanelNavigation>
            </Panel>
            <div className={"panel--under-panel"}>
                <Link className={'text-underline text-bold'} to={'/'}>
                    Повернутися до входу
                </Link>
            </div>
        </>
    );
}

export default RestorePassword;

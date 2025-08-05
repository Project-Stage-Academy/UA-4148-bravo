import { Link, useNavigate } from 'react-router-dom';
import Panel, { PanelBody, PanelNavigation, PanelTitle } from '../../components/Panel/panel';
import Button from '../../components/Button/button';
import { useState } from 'react';
import { Validator } from '../../utils/validation/validate';
import { restorePassword } from '../../api';
import HiddenInput from '../../components/PasswordInput/hiddenInput';

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
    const handleError = (error) => {
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
                        <div
                            className={
                                'content--text-container content--text-container__margin'
                            }
                        >
                            <div className={'content--substring-container'}>
                                <span className={'content--text'}>Пароль</span>
                                <p className={'content--subtext'}>
                                    Пароль повинен мати 8+ символів, містити
                                    принаймні велику, малу літеру (A..Z, a..z)
                                    та цифру (0..9).
                                </p>
                            </div>
                        </div>
                        <HiddenInput
                            name="password"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={formData.password}
                            onChange={handleChange}
                            className={errors['password'] ? 'input__error-border-color' : ''}
                        />
                        { errors['password'] ? <p className={"panel--danger-text"}>{ errors['password'] }</p> : "" }
                    </div>
                    <div>
                        <div className={'content--text-container content--text-container__margin'}>
                            <span className={'content--text'}>
                                        Повторіть пароль
                                    </span>
                        </div>
                        <HiddenInput
                            name="confirmPassword"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={formData.confirmPassword}
                            onChange={handleChange}
                            className={(errors['confirmPassword'] || errors['confirmPassword-passwords-dont-match'])
                                ? 'input__error-border-color' : ''}
                        />
                        { errors['confirmPassword'] ? <p className={"panel--danger-text"}>{ errors["confirmPassword"] }</p> : "" }
                    </div>
                    { errors['unexpected'] ? <p className={"panel--danger-text"}>{ errors['unexpected'] }</p> : ""}
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

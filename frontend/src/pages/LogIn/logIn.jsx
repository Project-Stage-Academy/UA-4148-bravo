import './logIn.css';
import Panel, {
    PanelBody,
    PanelBodyBottomLink,
    PanelBodyTitle,
    PanelNavigation,
    PanelTitle,
} from '../../components/Panel/panel';
import TextInput from '../../components/TextInput/textInput';
import HiddenInput from '../../components/HiddenInput/hiddenInput';
import Button from '../../components/Button/button';
import { Link, useNavigate } from 'react-router-dom';
import { Validator } from '../../utils/validation/validate';
import { useMemo, useState } from 'react';
import { useAuthContext } from '../../provider/AuthProvider/authProvider';
import bruteForce from "../../utils/bruteForce/bruteForce";
import { useFormWithProtection } from '../../hooks/useFormWithProtection/useFormWithProtection';

/**
 * LogInPage component
 * @returns {JSX.Element}
 */
function LogInPage() {
    const { login } = useAuthContext();

    // Form with protection hook
    const {
        formData, setFormData,
        errors, setErrors,
        attempts, setAttempts,
        isLocked, setIsLocked,
        isDisabled, navigate,
    } = useFormWithProtection({
        email: "",
        password: "",
        unexpected: "",
    });

    // Function to handle server-side errors
    const handleError = (error) => {
        if (error?.response && error?.response?.status === 404) {
            setErrors(prev => ({
                ...prev,
                unexpected: Validator.serverSideErrorMessages.noUserFoundByProvidedData
            }));
        } else {
            setErrors(prev => ({
                ...prev,
                unexpected: Validator.serverSideErrorMessages.unexpected
            }));
        }
    };

    // Function to handle form submission
    const handleSubmit = () => {
        if (isLocked) return;
        setIsLocked(true);

        const validationErrors = Validator.validate(
            formData
        );
        setErrors(validationErrors);

        if (Object.values(validationErrors).every(value => value === null)) {
            login(formData.email, formData.password)
                .then(() => navigate('/'))
                .catch((error) => bruteForce(error, {
                    attempts,
                    setAttempts,
                    setIsLocked,
                    handleError
                }));
        } else {
            console.warn('Errors:', validationErrors);
        }
        setIsLocked(false);
    };

    // Function to handle input changes
    const handleChange = (e) => {
        Validator.handleChange(e, formData, setFormData, setErrors);
    };

    return (
        <>
            <Panel aria-labelledby="login-form-title">
                <PanelTitle id="login-form-title">Вхід на платформу</PanelTitle>
                <PanelBody>
                    <div>
                        <PanelBodyTitle
                            id="email-label"
                            title={'Електронна пошта'}
                            className={'content--text-container__margin'}
                            required={false}
                        />
                        <TextInput
                            id="email"
                            name="email"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={formData.email}
                            onChange={handleChange}
                            placeholder={'Введіть свою електронну пошту'}
                            className={
                                errors['email'] && 'input__error-border-color'
                            }
                            aria-labelledby="email-label"
                            aria-describedby={errors['email'] ? 'email-error' : undefined}
                            aria-invalid={!!errors['email']}
                            aria-required="true"
                        />
                        {errors['email'] && (
                            <p id="email-error"
                               className={'panel--danger-text'}
                               role="alert"
                            >
                                {errors['email']}
                            </p>
                        )}
                    </div>
                    <div>
                        <PanelBodyTitle
                            id="password-label"
                            title={'Пароль'}
                            className={'content--text-container__margin'}
                            required={false}
                        />
                        <HiddenInput
                            id="password"
                            name="password"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={formData.password}
                            onChange={handleChange}
                            placeholder={'Введіть пароль'}
                            className={
                                errors['password'] && 'input__error-border-color'
                            }
                            aria-labelledby="password-label"
                            aria-describedby={errors['password'] ? 'password-error' : undefined}
                            aria-invalid={!!errors['password']}
                            aria-required="true"
                        />
                        {errors['password'] && (
                            <p id="password-error"
                               className={'panel--danger-text'}
                               role="alert"
                            >
                                {errors['password']}
                            </p>
                        )}
                        <PanelBodyBottomLink
                            linkText="Забули пароль?"
                            to="/auth/forgot"
                        />
                    </div>
                    {!isLocked && attempts >= 3 - 1 && (
                        <p className={'content--text'}>
                            Залишилося спроб: {5 - attempts}
                        </p>
                    )}
                    {isLocked && (
                        <p className={'panel--danger-text'}>
                            Повторіть спробу через 30 секунд
                        </p>
                    )}
                    {errors['unexpected'] && (
                        <p className={'panel--danger-text'}>
                            {errors['unexpected']}
                        </p>
                    )}
                </PanelBody>
                <PanelNavigation>
                    <Button
                        onClick={handleSubmit}
                        disabled={isDisabled || isLocked}
                        className={'button__padding panel--button'}
                        type="submit"
                    >
                        Увійти
                    </Button>
                </PanelNavigation>
            </Panel>
            <div className={'panel--under-panel'}>
                <span>Вперше на нашому сайті?</span>
                <Link className={'text-underline text-bold'} to={'/auth/register'}>
                    Зареєструйтесь
                </Link>
            </div>
        </>
    );
}

export default LogInPage;

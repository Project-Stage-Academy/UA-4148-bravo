import './registration.css';
import { Link, useNavigate } from 'react-router-dom';
import { Validator } from '../../utils/validation/validate';
import Button from '../../components/Button/button';
import Panel, { PanelBody, PanelBodyTitle, PanelNavigation, PanelTitle } from '../../components/Panel/panel';
import TextInput from '../../components/TextInput/textInput';
import HiddenInput from '../../components/HiddenInput/hiddenInput';
import { useAuthContext } from '../../provider/AuthProvider/authProvider';
import bruteForce from '../../utils/bruteForce/bruteForce';
import { useFormWithProtection } from '../../hooks/useFormWithProtection';
import { useFormWithServerErrors } from '../../hooks/useFormWithServerErrors';

/**
 * Registration component handles user registration.
 * It includes form fields for company name, email, password, confirmation password,
 * last name, first name, representation of the company, and business type.
 * It validates the input data and submits the registration request.
 * If the registration is successful, it navigates to the confirmation page.
 * If there are validation errors or server-side errors, it displays appropriate messages.
 * @returns {JSX.Element}
 */
function Registration() {
    // This component handles user registration
    const { setUser, register } = useAuthContext();

    // Hook to navigate programmatically
    const navigate = useNavigate();

    // Brute force max attempts constant
    const MAX_ATTEMPTS = 5;

    // Form with protection hook
    const form = useFormWithProtection({
        email: "",
        password: "",
        confirmPassword: "",
        lastName: "",
        firstName: "",
        unexpected: "",
    });

    // Function to handle server-side errors
    const extractError = (error) => {
        if (error?.response?.data?.errors?.email) {
            return { email: Validator.serverSideErrorMessages.emailAlreadyExist };
        } else {
            return { unexpected: Validator.serverSideErrorMessages.unexpected };
        }
    };

    // Function to handle form submission with brute force protection
    const doSubmit = ({ form, handleError }) => {
        register(
            form.data.email,
            form.data.firstName,
            form.data.lastName,
            form.data.password,
            form.data.confirmPassword
        )
            .then((res) => {
                setUser({
                    id: res.data.user_id,
                    email: res.data.email
                });

                navigate('/auth/register/confirm');
            })
            .catch((error) => bruteForce(error, {
                attempts: form.attempts,
                setAttempts: form.setAttempts,
                setIsLocked: form.setIsLocked,
                handleError
            }))
            .finally(() => form.setIsLocked(false));
    };

    const { handleSubmit, handleChange } = useFormWithServerErrors({
        form,
        navigate,
        extractError,
        doSubmit,
    });

    return (
        <>
            <Panel aria-labelledby="register-form-title">
                <PanelTitle id="register-form-title">Реєстрація</PanelTitle>
                <PanelBody>
                    <PanelBodyTitle
                        title={'Обов’язкові поля позначені зірочкою'}
                    />
                    <div>
                        <PanelBodyTitle
                            id="email-label"
                            title={'Електронна пошта'}
                            className={'content--text-container__margin'}
                        />
                        <TextInput
                            id="email"
                            name="email"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={form.data.email}
                            onChange={handleChange}
                            placeholder={'Введіть свою електронну пошту'}
                            className={
                                form.errors['email'] && 'input__error-border-color'
                            }
                            aria-labelledby="email-label"
                            aria-describedby={form.errors['email'] ? 'email-error' : undefined}
                            aria-invalid={!!form.errors['email']}
                            aria-required="true"
                        />
                        {form.errors['email'] && (
                            <p id="email-error"
                               className={'panel--danger-text'}
                               role="alert"
                            >
                                {form.errors['email']}
                            </p>
                        )}
                    </div>
                    <div>
                        <PanelBodyTitle
                            id="password-label"
                            title={'Пароль'}
                            className={'content--text-container__margin'}
                        >
                            Пароль повинен мати 8+ символів, містити принаймні
                            велику, малу літеру (A..Z, a..z) та цифру (0..9).
                        </PanelBodyTitle>
                        <HiddenInput
                            id="password"
                            name="password"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={form.data.password}
                            onChange={handleChange}
                            placeholder={'Введіть пароль'}
                            className={
                                form.errors['password'] && 'input__error-border-color'
                            }
                            aria-labelledby="password-label"
                            aria-describedby={form.errors['password'] ? 'password-error' : undefined}
                            aria-invalid={!!form.errors['password']}
                            aria-required="true"
                        />
                        {form.errors['password'] && (
                            <p id="password-error"
                               className={'panel--danger-text'}
                               role="alert"
                            >
                                {form.errors['password']}
                            </p>
                        )}
                    </div>
                    <div>
                        <PanelBodyTitle
                            id="confirmPassword-label"
                            title={'Повторіть пароль'}
                            className={'content--text-container__margin'}
                        />
                        <HiddenInput
                            id="confirmPassword"
                            name="confirmPassword"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={form.data.confirmPassword}
                            onChange={handleChange}
                            placeholder={'Введіть пароль ще раз'}
                            className={
                                form.errors['confirmPassword'] &&
                                'input__error-border-color'
                            }
                            aria-labelledby="confirmPassword-label"
                            aria-describedby={form.errors['confirmPassword'] ? 'confirmPassword-error' : undefined}
                            aria-invalid={!!form.errors['confirmPassword']}
                            aria-required="true"
                        />
                        {form.errors['confirmPassword'] && (
                            <p id="confirmPassword-error"
                               className={'panel--danger-text'}
                               role="alert"
                            >
                                {form.errors['confirmPassword']}
                            </p>
                        )}
                    </div>
                    <div>
                        <PanelBodyTitle
                            id="lastName-label"
                            title={'Прізвище'}
                            className={'content--text-container__margin'}
                        />
                        <TextInput
                            id="lastName"
                            name="lastName"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={form.data.lastName}
                            onChange={handleChange}
                            placeholder={'Введіть ваше прізвище'}
                            className={
                                form.errors['lastName'] &&
                                'input__error-border-color'
                            }
                            aria-labelledby="lastName-label"
                            aria-describedby={form.errors['lastName'] ? 'lastName-error' : undefined}
                            aria-invalid={!!form.errors['lastName']}
                            aria-required="true"
                        />
                        {form.errors['lastName'] && (
                            <p id="lastName-error"
                               className={'panel--danger-text'}
                               role="alert"
                            >
                                {form.errors['lastName']}
                            </p>
                        )}
                    </div>
                    <div>
                        <PanelBodyTitle
                            id="firstName-label"
                            title={'Ім‘я'}
                            className={'content--text-container__margin'}
                        />
                        <TextInput
                            name="firstName"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={form.data.firstName}
                            onChange={handleChange}
                            placeholder={'Введіть ваше ім’я'}
                            className={
                                form.errors['firstName'] &&
                                'input__error-border-color'
                            }
                            aria-labelledby="firstName-label"
                            aria-describedby={form.errors['firstName'] ? 'firstName-error' : undefined}
                            aria-invalid={!!form.errors['firstName']}
                            aria-required="true"
                        />
                        {form.errors['firstName'] && (
                            <p id="firstName-error"
                               className={'panel--danger-text'}
                               role="alert"
                            >
                                {form.errors['firstName']}
                            </p>
                        )}
                    </div>
                    {!form.isLocked && form.attempts >= (MAX_ATTEMPTS - 2 - 1) && (
                        <p className={'content--text'}
                           role="alert"
                        >
                            Залишилося спроб: {MAX_ATTEMPTS - form.attempts}
                        </p>
                    )}
                    {form.isLocked && form.attempts >= (MAX_ATTEMPTS + 1 - 1) && (
                        <p className={'panel--danger-text'}>
                            Повторіть спробу через 30 секунд
                        </p>
                    )}
                    {form.errors['unexpected'] && (
                        <p className={'panel--danger-text'}>
                            {form.errors['unexpected']}
                        </p>
                    )}
                </PanelBody>
                <PanelNavigation>
                    <Button
                        onClick={handleSubmit}
                        disabled={form.isDisabled || form.isLocked}
                        className={'button__padding panel--button'}
                        type="submit"
                    >
                        Зареєструватися
                    </Button>
                </PanelNavigation>
            </Panel>
            <div className={'panel--under-panel'}>
                <span>Ви вже зареєстровані у нас?</span>
                <Link className={'text-underline text-bold'} to={'/auth/login'}>
                    Увійти
                </Link>
            </div>
        </>
    );
}

export default Registration;

import './registration.css';
import { Link } from 'react-router-dom';
import { Validator } from '../../utils/validation/validate';
import Button from '../../components/Button/button';
import Panel, { PanelBody, PanelBodyTitle, PanelNavigation, PanelTitle } from '../../components/Panel/panel';
import TextInput from '../../components/TextInput/textInput';
import HiddenInput from '../../components/HiddenInput/hiddenInput';
import { useAuthContext } from '../../provider/AuthProvider/authProvider';
import bruteForce from '../../utils/bruteForce/bruteForce';
import { useFormWithProtection } from '../../hooks/useFormWithProtection/useFormWithProtection';

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

    // Form with protection hook
    const {
        formData, setFormData,
        errors, setErrors,
        attempts, setAttempts,
        isLocked, setIsLocked,
        navigate,
    } = useFormWithProtection({
        email: "",
        password: "",
        confirmPassword: "",
        lastName: "",
        firstName: "",
        unexpected: "",
    });

    // Function to handle server-side errors
    const handleError = (error) => {
        if (error?.response && error?.response?.data?.errors?.email) {
            setErrors(prev => ({
                ...prev,
                email: Validator.serverSideErrorMessages.emailAlreadyExist
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
            register(
                formData.email,
                formData.firstName,
                formData.lastName,
                formData.password,
                formData.confirmPassword
            )
                .then((res) => {
                    setUser({
                        id: res.data.user_id,
                        email: res.data.email
                    });

                    navigate('/auth/register/confirm');
                })
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
        return Validator.handleChange(
            e,
            formData,
            setFormData,
            setErrors
        );
    };

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
                            value={formData.confirmPassword}
                            onChange={handleChange}
                            placeholder={'Введіть пароль ще раз'}
                            className={
                                errors['confirmPassword'] &&
                                'input__error-border-color'
                            }
                            aria-labelledby="confirmPassword-label"
                            aria-describedby={errors['confirmPassword'] ? 'confirmPassword-error' : undefined}
                            aria-invalid={!!errors['confirmPassword']}
                            aria-required="true"
                        />
                        {errors['confirmPassword'] && (
                            <p id="confirmPassword-error"
                               className={'panel--danger-text'}
                               role="alert"
                            >
                                {errors['confirmPassword']}
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
                            value={formData.lastName}
                            onChange={handleChange}
                            placeholder={'Введіть ваше прізвище'}
                            className={
                                errors['lastName'] &&
                                'input__error-border-color'
                            }
                            aria-labelledby="lastName-label"
                            aria-describedby={errors['lastName'] ? 'lastName-error' : undefined}
                            aria-invalid={!!errors['lastName']}
                            aria-required="true"
                        />
                        {errors['lastName'] && (
                            <p id="lastName-error"
                               className={'panel--danger-text'}
                               role="alert"
                            >
                                {errors['lastName']}
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
                            value={formData.firstName}
                            onChange={handleChange}
                            placeholder={'Введіть ваше ім’я'}
                            className={
                                errors['firstName'] &&
                                'input__error-border-color'
                            }
                            aria-labelledby="firstName-label"
                            aria-describedby={errors['firstName'] ? 'firstName-error' : undefined}
                            aria-invalid={!!errors['firstName']}
                            aria-required="true"
                        />
                        {errors['firstName'] && (
                            <p id="firstName-error"
                               className={'panel--danger-text'}
                               role="alert"
                            >
                                {errors['firstName']}
                            </p>
                        )}
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
                        disabled={isLocked}
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

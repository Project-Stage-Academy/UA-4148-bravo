import './forgotPassword.css';
import Panel, { PanelBody, PanelBodyTitle, PanelNavigation, PanelTitle } from '../../components/Panel/panel';
import Button from '../../components/Button/button';
import { Link } from 'react-router-dom';
import TextInput from '../../components/TextInput/textInput';
import { Validator } from '../../utils/validation/validate';
import { useAuthContext } from '../../provider/AuthProvider/authProvider';
import bruteForce from '../../utils/bruteForce/bruteForce';
import { useFormWithProtection } from '../../hooks/useFormWithProtection/useFormWithProtection';

/**
 * ForgotPassword component
 * @returns {JSX.Element}
 */
function ForgotPassword() {
    const { requestReset } = useAuthContext();

    // Form with protection hook
    const {
        formData, setFormData,
        errors, setErrors,
        attempts, setAttempts,
        isLocked, setIsLocked,
        isDisabled, navigate,
    } = useFormWithProtection({
        email: "",
        unexpected: "",
    });

    // Override message for email error
    const errorValidationMessage = {
        email: 'Введіть адресу електронної пошти у форматі name@example.com'
    };

    // Function to handle server-side errors
    const handleError = (error) => {
        if (error?.response && error?.response?.data?.email) {
            setErrors(prev => ({
                ...prev,
                email: Validator.serverSideErrorMessages.emailNotExists
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
            requestReset(formData.email)
                .then(() => navigate('/auth/forgot/done'))
                .catch((error) => bruteForce(error, {
                    attempts,
                    setAttempts,
                    setIsLocked,
                    handleError
                }));
        } else {
            console.log("Errors:", validationErrors);
        }
        setIsLocked(false);
    }

    // Function to handle input changes
    const handleChange = (e) => {
        Validator.handleChange(e, formData, setFormData, setErrors,
            Validator.errorZeroLengthMessages, errorValidationMessage,
        );
    };

    return (
        <>
            <Panel aria-labelledby="forgot-password-form-title">
                <PanelTitle id="forgot-password-form-title"
                            aria-describedby="forgot-password-help1 forgot-password-help2"
                >
                    Забули пароль?
                </PanelTitle>
                <PanelBody>
                    <div>
                        <p id="forgot-password-help1"
                           className={'panel--font-size'}
                        >
                            Введіть електронну адресу вказану при реєстрації для відновлення паролю.
                        </p>
                        <p id="forgot-password-help2"
                           className={'panel--font-size'}
                        >
                            На зазначену вами електронну пошту буде відправлено листа з посиланням для відновлення паролю.
                        </p>
                    </div>
                    <div>
                        <PanelBodyTitle title={'Електронна пошта'} required={false} />
                        <TextInput
                            name="email"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={formData.email}
                            onChange={handleChange}
                            placeholder={'Введіть свою електронну пошту'}
                            className={errors['email'] && 'input__error-border-color'}
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
                    {!isLocked && attempts >= 3 - 1 && (
                        <p className={'content--text'}
                           role="alert"
                        >
                            Залишилося спроб: {5 - attempts}
                        </p>
                    )}
                    {isLocked && (
                        <p className={'panel--danger-text'}
                           role="alert"
                        >
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
                        className={'button__padding panel--button'}
                        disabled={isDisabled || isLocked}
                        type="submit"
                    >
                        Відновити пароль
                    </Button>
                </PanelNavigation>
            </Panel>
            <div className={"panel--under-panel"}>
                <span>Я згадав свій пароль.</span>
                <Link className={'text-underline text-bold'} to={'/auth/login'}>
                    Повернутися до входу
                </Link>
            </div>
        </>
    );
}

export default ForgotPassword;

import './forgotPassword.css';
import Panel, { PanelBody, PanelBodyTitle, PanelNavigation, PanelTitle } from '../../components/Panel/panel';
import Button from '../../components/Button/button';
import { Link, useNavigate } from 'react-router-dom';
import TextInput from '../../components/TextInput/textInput';
import { Validator } from '../../utils/validation/validate';
import { useAuthContext } from '../../provider/AuthProvider/authProvider';
import bruteForce from '../../utils/bruteForce/bruteForce';
import { useFormWithProtection } from '../../hooks/useFormWithProtection';
import { useFormWithServerErrors } from '../../hooks/useFormWithServerErrors';

/**
 * ForgotPassword component
 * @returns {JSX.Element}
 */
function ForgotPassword() {
    const { requestReset } = useAuthContext();

    // Hook to navigate programmatically
    const navigate = useNavigate();

    // Brute force max attempts constant
    const MAX_ATTEMPTS = 5;

    // Form with protection hook
    const form = useFormWithProtection({
        email: "",
        unexpected: "",
    });

    // Override message for email error
    const errorValidationMessages = {
        email: 'Введіть адресу електронної пошти у форматі name@example.com'
    };

    // Function to handle server-side errors
    const extractError = (error) => {
        if (error?.response?.data?.email) {
            return { email: Validator.serverSideErrorMessages.emailNotExists };
        } else {
            return { unexpected: Validator.serverSideErrorMessages.unexpected };
        }
    };

    // Function to handle form submission with brute force protection
    const doSubmit = ({ form, handleError }) => {
        requestReset(form.data.email)
            .then(() => navigate('/auth/forgot/done'))
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
        handleChangeCustom: (e, form) => {
            Validator.handleChange(
                e,
                form.data,
                form.setData,
                form.setErrors,
                Validator.errorZeroLengthMessages,
                errorValidationMessages,
            );
        }
    });

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
                            value={form.data.email}
                            onChange={handleChange}
                            placeholder={'Введіть свою електронну пошту'}
                            className={form.errors['email'] && 'input__error-border-color'}
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
                    {!form.isLocked && form.attempts >= (MAX_ATTEMPTS - 2 - 1) && (
                        <p className={'content--text'}
                           role="alert"
                        >
                            Залишилося спроб: {MAX_ATTEMPTS - form.attempts}
                        </p>
                    )}
                    {form.isLocked && form.attempts >= (MAX_ATTEMPTS + 1 - 1) && (
                        <p className={'panel--danger-text'}
                           role="alert"
                        >
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
                        className={'button__padding panel--button'}
                        disabled={form.isDisabled || form.isLocked}
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

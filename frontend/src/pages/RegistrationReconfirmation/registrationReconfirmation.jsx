import { Validator } from '../../utils/validation/validate';
import Button from '../../components/Button/button';
import Panel, { PanelBody, PanelBodyTitle, PanelNavigation, PanelTitle } from '../../components/Panel/panel';
import TextInput from '../../components/TextInput/textInput';
import { useAuthContext } from '../../provider/AuthProvider/authProvider';
import { useFormWithProtection } from '../../hooks/useFormWithProtection';
import { useFormWithServerErrors } from '../../hooks/useFormWithServerErrors';
import { useNavigate } from 'react-router-dom';

/**
 * Component for reconfirming user registration by resending the activation email.
 * It allows users to enter their email address to receive a new activation link.
 * The component validates the input and handles errors from the server.
 * If the email is already registered, it shows an error message.
 * If the email is valid, it sends a request to register the user and navigates to
 * the confirmation page upon success.
 * @returns {JSX.Element}
 */
function RegistrationReconfirmation() {
    const { user, setUser, resendRegisterEmail } = useAuthContext();

    // Hook to navigate programmatically
    const navigate = useNavigate();

    // Form with protection hook
    const form = useFormWithProtection({
        email: "",
        unexpected: "",
    });

    // Function to handle server-side errors
    const extractError = (error) => {
        if (error.response.status === 401) {
            return { email: Validator.serverSideErrorMessages.emailAlreadyExist };
        } else {
            return { unexpected: Validator.serverSideErrorMessages.unexpected };
        }
    };

    // Function to handle form submission with brute force protection
    const doSubmit = ({ form, handleError }) => {
        resendRegisterEmail(form.data.email, user.id)
            .then(() => {
                setUser({
                    email: form.data.email
                });

                navigate('/auth/register/confirm');
            })
            .catch(handleError)
            .finally(() => form.setIsLocked(false));
    };

    // Function to handle cancellation
    const handleCancel = () => {
        navigate("/");
    };

    const { handleSubmit, handleChange } = useFormWithServerErrors({
        form,
        navigate,
        extractError,
        doSubmit,
    });

    return (
        <Panel className={'panel__margin-large'}
               aria-labelledby="registrationReconfirmation-title"
        >
            <PanelTitle id="registrationReconfirmation-title"
                        aria-describedby="registrationReconfirmation-help1 registrationReconfirmation-help2"
            >
                Надіслати лист для активації ще раз
            </PanelTitle>
            <PanelBody>
                <div>
                    <p id="registrationReconfirmation-help1"
                       className={'panel--font-size'}
                    >
                        Введіть електронну адресу вказану при реєстрації для
                        повторного надіслення листа.
                    </p>
                    <p id="registrationReconfirmation-help2"
                       className={'panel--font-size'}
                    >
                        На зазначену Вами електронну пошту буде відправлено
                        листа з посиланням для активації.
                    </p>
                </div>
                <div>
                    <PanelBodyTitle title={'Електронна пошта'} />
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
                {form.errors['unexpected'] && <p className={'panel--danger-text'}>{ form.errors['unexpected'] }</p>}
            </PanelBody>
            <PanelNavigation>
                <Button
                    onClick={handleSubmit}
                    className={'button__padding panel--button'}
                    type="submit"
                >
                    Надіслати
                </Button>
                <Button
                    variant="secondary"
                    onClick={handleCancel}
                    disabled={form.isLocked}
                    className={'button__padding panel--button'}
                >
                    Скасувати
                </Button>
            </PanelNavigation>
        </Panel>
    );
}

export default RegistrationReconfirmation;

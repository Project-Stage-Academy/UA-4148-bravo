import { useState } from 'react';
import { Validator } from '../../utils/validation/validate';
import { useNavigate } from 'react-router-dom';
import Button from '../../components/Button/button';
import Panel, { PanelBody, PanelBodyTitle, PanelNavigation, PanelTitle } from '../../components/Panel/panel';
import TextInput from '../../components/TextInput/textInput';
import { useAuthContext } from '../../provider/AuthProvider/authProvider';

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

    // State to hold form data
    const [formData, setFormData] = useState(
        {
            email: "",
            unexpected: ""
        });

    // State to hold validation errors
    const [errors, setErrors] = useState({});

    // Function to handle server-side errors
    const handleError = (error) => {
        if (error.response && error.response.status === 401) {
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
        const validationErrors = Validator.validate(formData);
        setErrors(validationErrors);

        if (Object.values(validationErrors).every(value => value === null)) {
            resendRegisterEmail(formData.email, user.id)
                .then(() => {
                    setUser({
                        email: formData.email
                    });

                    navigate('/auth/register/confirm');
                })
                .catch(handleError);
        } else {
            console.log("Errors:", validationErrors);
        }
    }

    // Function to handle cancellation
    const handleCancel = () => {
        navigate("/");
    }

    // Function to handle input changes
    const handleChange = (e) => {
        Validator.handleChange(
            e,
            formData,
            setFormData,
            setErrors
        );
    };

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
                {errors['unexpected'] && <p className={'panel--danger-text'}>{ errors['unexpected'] }</p>}
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
                    className={'button__padding panel--button'}
                >
                    Скасувати
                </Button>
            </PanelNavigation>
        </Panel>
    );
}

export default RegistrationReconfirmation;

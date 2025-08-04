import "./registerReconfirmation.css";
import { useState } from 'react';
import { Validator } from '../../utils/validation/validate';
import { useNavigate } from 'react-router-dom';
import Button from '../Button/button';
import { registerUser } from '../../api';
import Panel, { PanelBody, PanelNavigation, PanelTitle } from '../Panel/panel';

/**
 * Component for reconfirming user registration by resending the activation email.
 * It allows users to enter their email address to receive a new activation link.
 * The component validates the input and handles errors from the server.
 * If the email is already registered, it shows an error message.
 * If the email is valid, it sends a request to register the user and navigates to
 * the confirmation page upon success.
 * @returns {JSX.Element}
 */
function RegisterReconfirmation() {
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
        if (error.response && error.response.status === 409) {
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
            registerUser(formData)
                .then(() => navigate('/auth/register/confirm'))
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
        <Panel className={"panel__margin-large"}>
            <PanelTitle>Надіслати лист для активації ще раз</PanelTitle>
            <PanelBody>
                <div>
                    <p className={"panel--font-size"}>
                        Введіть електронну адресу вказану при реєстрації для повторного надіслення листа.
                    </p>
                    <p className={"panel--font-size"}>На зазначену Вами електронну пошту буде відправлено листа з посиланням для активації.</p>
                </div>
                <div>
                    <div className={'content--text-container__margin'}>
                        <span
                            className={
                                'content--text content--text__starred content--text__margin'
                            }
                        >
                            *
                        </span>
                        <span className={'content--text'}>
                            Електронна пошта
                        </span>
                    </div>
                    <input
                        type="text"
                        name="email"
                        autoComplete="off"
                        autoCorrect="off"
                        spellCheck="false"
                        value={formData.email}
                        onChange={handleChange}
                        placeholder={'Введіть свою електронну пошту'}
                        className={`input input-text input__width ${(errors['email'] || errors['email-exist']) ? 'input__error-border-color' : ''}`}
                    />
                    { errors['email'] ? <p className={"panel--danger-text"}>{ errors['email'] }</p> : ""}
                </div>
                { errors['unexpected'] ? <p className={"panel--danger-text"}>{ errors['unexpected'] }</p> : ""}
            </PanelBody>
            <PanelNavigation>
                <Button
                    onClick={handleSubmit}
                    className={'button__padding panel--button'}
                >
                    Надіслати
                </Button>
                <Button
                    variant='secondary'
                    onClick={handleCancel}
                    className={'button__padding panel--button'}
                >
                    Скасувати
                </Button>
            </PanelNavigation>
        </Panel>
    );
}

export default RegisterReconfirmation;

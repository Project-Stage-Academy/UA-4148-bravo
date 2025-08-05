import './forgotPassword.css';
import Panel, { PanelBody, PanelBodyTitle, PanelNavigation, PanelTitle } from '../../components/Panel/panel';
import Button from '../../components/Button/button';
import { Link, useNavigate } from 'react-router-dom';
import TextInput from '../../components/TextInput/textInput';
import { Validator } from '../../utils/validation/validate';
import { useState } from 'react';
import { forgotPassword } from '../../api';

/**
 * ForgotPassword component
 * @returns {JSX.Element}
 */
function ForgotPassword() {
    // Hook to navigate programmatically
    const navigate = useNavigate();

    // State to hold form data
    const [formData, setFormData] = useState(
        {
            email: "",
            unexpected: ""
        });

    const errorValidationMessage = {
        email: 'Введіть адресу електронної пошти у форматі name@example.com'
    };

    // State to hold validation errors
    const [errors, setErrors] = useState({});

    // Function to handle server-side errors
    const handleError = (error) => {
        if (error.response && error.response.status === 409) {
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
        const validationErrors = Validator.validate(formData);
        setErrors(validationErrors);

        if (Object.values(validationErrors).every(value => value === null)) {
            forgotPassword(formData)
                .then(() => navigate('/forgot-password/done'))
                .catch(handleError);
        } else {
            console.log("Errors:", validationErrors);
        }
    }

    // Function to handle input changes
    const handleChange = (e) => {
        Validator.handleChange(
            e,
            formData,
            setFormData,
            setErrors,
            Validator.errorZeroLengthMessages,
            errorValidationMessage,
        );
    };

    return (
        <>
            <Panel>
                <PanelTitle>Забули пароль?</PanelTitle>
                <PanelBody>
                    <div>
                        <p className={'panel--font-size'}>
                            Введіть електронну адресу вказану при реєстрації для відновлення паролю.
                        </p>
                        <p className={'panel--font-size'}>
                            На зазначену вами електронну пошту буде відправлено листа з посиланням для відновлення паролю.
                        </p>
                    </div>
                    <div>
                        <PanelBodyTitle title={'Електронна пошта'} />
                        <TextInput
                            name="email"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={formData.email}
                            onChange={handleChange}
                            placeholder={'Введіть свою електронну пошту'}
                            className={errors['email'] && 'input__error-border-color'}
                        />
                        {errors['email'] && <p className={'panel--danger-text'}>{ errors['email'] }</p>}
                    </div>
                    {errors['unexpected'] && <p className={'panel--danger-text'}>{ errors['unexpected'] }</p>}
                </PanelBody>
                <PanelNavigation>
                    <Button
                        onClick={handleSubmit}
                        className={'button__padding panel--button'}
                        disabled={!formData.email || errors['email'] || errors['unexpected']}
                    >
                        Відновити пароль
                    </Button>
                </PanelNavigation>
            </Panel>
            <div className={"panel--under-panel"}>
                <span>Я згадав свій пароль.</span>
                <Link className={'text-underline text-bold'} to={'/'}>
                    Повернутися до входу
                </Link>
            </div>
        </>
    );
}

export default ForgotPassword;

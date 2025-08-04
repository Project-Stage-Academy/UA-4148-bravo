import "./registerReconfirmation.css";
import { useState } from 'react';
import { Validator } from '../../utils/validation/validate';
import { useNavigate } from 'react-router-dom';
import Button from '../Button/button';
import { registerUser } from '../../api';
import Panel, { PanelBody, PanelNavigation, PanelTitle } from '../Panel/panel';

function RegisterReconfirmation() {
    const navigate = useNavigate();

    const [formData, setFormData] = useState(
        {
            email: "",
            unexpected: ""
        });

    const [errors, setErrors] = useState({});

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

    const handleCancel = () => {
        navigate("/");
    }

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

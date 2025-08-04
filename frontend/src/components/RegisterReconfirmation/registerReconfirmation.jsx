import "./registerReconfirmation.css";
import { useState } from 'react';
import { Validator } from '../../utils/validation/validate';
import { useNavigate } from 'react-router-dom';

function RegisterReconfirmation() {
    const navigate = useNavigate();

    const [formData, setFormData] = useState({ email: "" });

    const [errors, setErrors] = useState({});

    const handleSubmit = () => {
        const validationErrors = Validator.validate(formData);
        setErrors(validationErrors);

        if (Object.keys(validationErrors).length === 0) {
            navigate("/auth/register/confirmation");
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
        <div className={'panel panel__margin panel__margin-large'}>
            <h2 className={'panel--title'}>Надіслати лист для активації ще раз</h2>
            <hr className={'panel--hr'} />
            <div className={'panel--content'}>
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
                    { errors['email'] ? <p className={"panel--error-text"}>{ errors['email'] }</p> : ""}
                </div>
            </div>
            <hr className={'panel--hr'} />
            <div className={"panel--navigation"}>
                <button
                    onClick={handleSubmit}
                    className={
                        'button button__padding button__primary-color panel--button'
                    }
                >
                    Надіслати
                </button>
                <button
                    onClick={handleCancel}
                    className={
                        'button button__padding button__secondary-color panel--button'
                    }
                >
                    Скасувати
                </button>
            </div>
        </div>
    );
}

export default RegisterReconfirmation;

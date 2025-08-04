import './registration.css';
import { Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { Validator } from '../../utils/validation/validate';
import Button from '../Button/button';
import { registerUser } from '../../api';
import Panel, { PanelBody, PanelNavigation, PanelTitle } from '../Panel/panel';

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
    const navigate = useNavigate();

    // State to hold form data
    const [formData, setFormData] = useState(
        {
            companyName: "",
            email: "",
            password: "",
            confirmPassword: "",
            lastName: "",
            firstName: "",
            representation: {
                company: false,
                startup: false
            },
            businessType: {
                individual: false,
                legal: false
            },
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
        const validationErrors = Validator.validate(
            formData
        );
        setErrors(validationErrors);

        if (Object.values(validationErrors).every(value => value === null)) {
            registerUser(formData)
                .then(() => navigate('/auth/register/confirm'))
                .catch(handleError);
        } else {
            console.log('Errors:', validationErrors);
        }
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
            <Panel>
                <PanelTitle>Реєстрація</PanelTitle>
                <PanelBody>
                    <div className={"content--text-container"}>
                            <span
                                className={
                                    'content--text content--text__starred content--text__margin'
                                }
                            >
                                *
                            </span>
                        <span className={'content--text'}>
                                Обов’язкові поля позначені зірочкою
                            </span>
                    </div>
                    <div>
                        <div className={'content--text-container content--text-container__margin'}>
                                <span
                                    className={
                                        'content--text content--text__starred content--text__margin'
                                    }
                                >
                                    *
                                </span>
                            <span className={'content--text'}>
                                    Назва компанії
                                </span>
                        </div>
                        <input
                            type="text"
                            name="companyName"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={formData.companyName}
                            onChange={handleChange}
                            placeholder={'Введіть назву вашої компанії'}
                            className={`input input-text input__width ${errors['companyName'] ? 'input__error-border-color' : ''}`}
                        />
                        { errors['companyName'] ? <p className={"panel--danger-text"}>{ errors['companyName'] }</p> : "" }
                    </div>
                    <div>
                        <div className={'content--text-container content--text-container__margin'}>
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
                    <div>
                        <div
                            className={
                                'content--text-container content--text-container__margin'
                            }
                        >
                                <span
                                    className={
                                        'content--text content--text__starred content--text__margin'
                                    }
                                >
                                    *
                                </span>
                            <div className={'content--substring-container'}>
                                <span className={'content--text'}>Пароль</span>
                                <p className={'content--subtext'}>
                                    Пароль повинен мати 8+ символів, містити
                                    принаймні велику, малу літеру (A..Z, a..z)
                                    та цифру (0..9).
                                </p>
                            </div>
                        </div>
                        <input
                            type="password"
                            name="password"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={formData.password}
                            onChange={handleChange}
                            placeholder={'Введіть пароль'}
                            className={`input input-text input__width ${errors['password'] ? 'input__error-border-color' : ''}`}
                        />
                        { errors['password'] ? <p className={"panel--danger-text"}>{ errors['password'] }</p> : "" }
                    </div>
                    <div>
                        <div className={'content--text-container content--text-container__margin'}>
                                <span
                                    className={
                                        'content--text content--text__starred content--text__margin'
                                    }
                                >
                                    *
                                </span>
                            <span className={'content--text'}>
                                    Повторіть пароль
                                </span>
                        </div>
                        <input
                            type="password"
                            name="confirmPassword"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={formData.confirmPassword}
                            onChange={handleChange}
                            placeholder={'Введіть пароль ще раз'}
                            className={`input input-text input__width ${(errors['confirmPassword'] || errors['confirmPassword-passwords-dont-match']) ? 'input__error-border-color' : ''}`}
                        />
                        { errors['confirmPassword'] ? <p className={"panel--danger-text"}>{ errors["confirmPassword"] }</p> : "" }
                    </div>
                    <div>
                        <div className={'content--text-container content--text-container__margin'}>
                                <span
                                    className={
                                        'content--text content--text__starred content--text__margin'
                                    }
                                >
                                    *
                                </span>
                            <span className={'content--text'}>Прізвище</span>
                        </div>
                        <input
                            type="text"
                            name="lastName"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={formData.lastName}
                            onChange={handleChange}
                            placeholder={'Введіть ваше прізвище'}
                            className={`input input-text input__width ${errors['lastName'] ? 'input__error-border-color' : ''}`}
                        />
                        { errors['lastName'] ? <p className={"panel--danger-text"}>{ errors["lastName"] }</p> : "" }
                    </div>
                    <div>
                        <div className={'content--text-container content--text-container__margin'}>
                                <span
                                    className={
                                        'content--text content--text__starred content--text__margin'
                                    }
                                >
                                    *
                                </span>
                            <span className={'content--text'}>Ім‘я</span>
                        </div>
                        <input
                            type="text"
                            name="firstName"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={formData.firstName}
                            onChange={handleChange}
                            placeholder={'Введіть ваше ім’я'}
                            className={`input input-text input__width ${errors['firstName'] ? 'input__error-border-color' : ''}`}
                        />
                        { errors['firstName'] ? <p className={"panel--danger-text"}>{ errors["firstName"] }</p> : "" }
                    </div>
                    <div>
                        <div className={'content--text-container content--text-container__margin'}>
                                <span
                                    className={
                                        'content--text content--text__starred content--text__margin'
                                    }
                                >
                                    *
                                </span>
                            <span className={'content--text'}>
                                    Кого ви представляєте?
                                </span>
                        </div>
                        <div className={"checkbox--container"}>
                            <div className={"checkbox--item"}>
                                <input
                                    type="checkbox"
                                    name="representation.company"
                                    checked={formData.representation.company}
                                    onChange={handleChange}
                                    className={`checkbox ${errors['representation'] ? 'checkbox__error-color' : 'checkbox__active-color'}`}
                                />
                                <label htmlFor="html" className={"panel--font-size"}>Зареєстрована компанія</label>
                            </div>
                            <div className={"checkbox--item"}>
                                <input
                                    type="checkbox"
                                    name="representation.startup"
                                    checked={formData.representation.startup}
                                    onChange={handleChange}
                                    className={`checkbox ${errors['representation'] ? 'checkbox__error-color' : 'checkbox__active-color'}`}
                                />
                                <label htmlFor="html" className={"panel--font-size"}>Стартап проєкт, який шукає інвестиції</label>
                            </div>
                        </div>
                        { errors['representation'] ? <p className={"panel--danger-text"}>{ errors["representation"] }</p> : "" }
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
                                    Який суб’єкт господарювання ви представляєте?
                                </span>
                        </div>
                        <div className={"checkbox--container"}>
                            <div className={"checkbox--item"}>
                                <input
                                    type="checkbox"
                                    name="businessType.individual"
                                    checked={formData.businessType.individual}
                                    onChange={handleChange}
                                    className={`checkbox ${errors['businessType'] ? 'checkbox__error-color' : 'checkbox__active-color'}`}
                                />
                                <label htmlFor="html" className={"panel--font-size"}>Фізична особа-підприємець</label>
                            </div>
                            <div className={"checkbox--item"}>
                                <input
                                    type="checkbox"
                                    name="businessType.legal"
                                    checked={formData.businessType.legal}
                                    onChange={handleChange}
                                    className={`checkbox ${errors['businessType'] ? 'checkbox__error-color' : 'checkbox__active-color'}`}
                                />
                                <label htmlFor="html" className={"panel--font-size"}>Юридична особа</label>
                            </div>
                        </div>
                        { errors['businessType'] ? <p className={"panel--danger-text"}>{ errors["businessType"] }</p> : "" }
                    </div>
                    { errors['unexpected'] ? <p className={"panel--danger-text"}>{ errors['unexpected'] }</p> : ""}
                    <div>
                        <span className={"panel--font-size"}>Реєструючись, я погоджуюсь з </span>
                        <Link className={"panel--font-size text-underline text-bold"} to={"/policy"}>правилами використання</Link>
                        <span className={"panel--font-size"}> сайту Craftmerge</span>
                    </div>
                </PanelBody>
                <PanelNavigation>
                    <Button
                        onClick={handleSubmit}
                        className={'button__padding panel--button'}
                    >
                        Зареєструватися
                    </Button>
                </PanelNavigation>
            </Panel>
            <div className={"panel--under-panel"}>
                <span>
                    Ви вже зареєстровані у нас?
                </span>
                <Link className={'text-underline text-bold'} to={'/login'}>
                    Увійти
                </Link>
            </div>
        </>
    );
}

export default Registration;

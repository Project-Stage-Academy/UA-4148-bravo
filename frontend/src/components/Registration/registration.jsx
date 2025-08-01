import './registration.css';
import { Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { Validator } from '../../utils/validation/validate';

function Registration() {
    const validator = new Validator();
    const navigate = useNavigate();

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
            }
        });

    const validators = {
        companyName: (value) => /^[\w\s]{2,}$/.test(value),
        email: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
        password: (value) => /^(?=.*[A-Z])(?=.*\d).{6,}$/.test(value),
        confirmPassword: (value, data) => typeof value === "string" && value.trim() !== "" && value === data.password,
        firstName: (value) => /^[A-Za-z]{2,}$/.test(value),
        lastName: (value) => /^[A-Za-z]{2,}$/.test(value),
        representation: (value) => Object.values(value).some(v => v),
        businessType: (value) => Object.values(value).some(v => v)
    };

    const [errors, setErrors] = useState({});

    const errorZeroLengthMessages = {
        companyName: "Не ввели назву компанії",
        email: "Не ввели електронну пошту",
        password: "Не ввели пароль",
        confirmPassword: "Не ввели пароль ще раз",
        firstName: "Не ввели ім’я",
        lastName: "Не ввели прізвище",
        representation: "Виберіть кого ви представляєте",
        businessType: "Виберіть який суб’єкт господарювання ви представляєте"
    }

    const errorValidationMessages = {
        companyName: "Назва компанії не відповідає вимогам",
        email: "Пошта не відповідає вимогам",
        password: "Пароль не відповідає вимогам",
        confirmPassword: "Паролі не співпадають. Будь ласка, введіть однакові паролі в обидва поля",
        firstName: "Ім’я не відповідає вимогам",
        lastName: "Прізвище не відповідає вимогам"
    }

    const handleSubmit = () => {
        const validationErrors = validator.validate(formData, validators, errorZeroLengthMessages, errorValidationMessages);
        setErrors(validationErrors);

        if (Object.keys(validationErrors).length === 0) {
            navigate("/auth/register/confirmation");
        } else {
            console.log("Errors:", validationErrors);
        }
    };

    return (
        <>
            <div className={'panel panel__margin'}>
                <h2 className={'panel--title'}>Реєстрація</h2>
                <hr className={'panel--hr'} />
                <div className={'panel--content'}>
                    <div>
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
                        <div className={'content--text-container__margin'}>
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
                            onChange={(e) => validator.handleChange(e, formData, setFormData, setErrors, validators, errorZeroLengthMessages, errorValidationMessages)}
                            placeholder={'Введіть назву вашої компанії'}
                            className={`input input-text input__width ${errors['companyName'] ? 'input__error-border-color' : ''}`}
                        />
                        { errors['companyName'] ? <p className={"panel--error-text"}>{ errors['companyName'] }</p> : "" }
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
                            onChange={(e) => validator.handleChange(e, formData, setFormData, setErrors, validators, errorZeroLengthMessages, errorValidationMessages)}
                            placeholder={'Введіть свою електронну пошту'}
                            className={`input input-text input__width ${(errors['email'] || errors['email-exist']) ? 'input__error-border-color' : ''}`}
                        />
                        { errors['email'] ? <p className={"panel--error-text"}>{ errors['email'] }</p> : ""}
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
                            onChange={(e) => validator.handleChange(e, formData, setFormData, setErrors, validators, errorZeroLengthMessages, errorValidationMessages)}
                            placeholder={'Введіть пароль'}
                            className={`input input-text input__width ${errors['password'] ? 'input__error-border-color' : ''}`}
                        />
                        { errors['password'] ? <p className={"panel--error-text"}>{ errors['password'] }</p> : "" }
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
                            onChange={(e) => validator.handleChange(e, formData, setFormData, setErrors, validators, errorZeroLengthMessages, errorValidationMessages)}
                            placeholder={'Введіть пароль ще раз'}
                            className={`input input-text input__width ${(errors['confirmPassword'] || errors['confirmPassword-passwords-dont-match']) ? 'input__error-border-color' : ''}`}
                        />
                        { errors['confirmPassword'] ? <p className={"panel--error-text"}>{ errors["confirmPassword"] }</p> : "" }
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
                            <span className={'content--text'}>Прізвище</span>
                        </div>
                        <input
                            type="text"
                            name="lastName"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={formData.lastName}
                            onChange={(e) => validator.handleChange(e, formData, setFormData, setErrors, validators, errorZeroLengthMessages, errorValidationMessages)}
                            placeholder={'Введіть ваше прізвище'}
                            className={`input input-text input__width ${errors['lastName'] ? 'input__error-border-color' : ''}`}
                        />
                        { errors['lastName'] ? <p className={"panel--error-text"}>{ errors["lastName"] }</p> : "" }
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
                            <span className={'content--text'}>Ім‘я</span>
                        </div>
                        <input
                            type="text"
                            name="firstName"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={formData.firstName}
                            onChange={(e) => validator.handleChange(e, formData, setFormData, setErrors, validators, errorZeroLengthMessages, errorValidationMessages)}
                            placeholder={'Введіть ваше ім’я'}
                            className={`input input-text input__width ${errors['firstName'] ? 'input__error-border-color' : ''}`}
                        />
                        { errors['firstName'] ? <p className={"panel--error-text"}>{ errors["firstName"] }</p> : "" }
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
                                Кого ви представляєте?
                            </span>
                        </div>
                        <div className={"checkbox--container"}>
                            <div className={"checkbox--item"}>
                                <input
                                    type="checkbox"
                                    name="representation.company"
                                    checked={formData.representation.company}
                                    onChange={(e) => validator.handleChange(e, formData, setFormData, setErrors, validators, errorZeroLengthMessages, errorValidationMessages)}
                                    className={`checkbox ${errors['representation'] ? 'checkbox__error-color' : 'checkbox__active-color'}`}
                                />
                                <label htmlFor="html" className={"panel--font-size"}>Зареєстрована компанія</label>
                            </div>
                            <div className={"checkbox--item"}>
                                <input
                                    type="checkbox"
                                    name="representation.startup"
                                    checked={formData.representation.startup}
                                    onChange={(e) => validator.handleChange(e, formData, setFormData, setErrors, validators, errorZeroLengthMessages, errorValidationMessages)}
                                    className={`checkbox ${errors['representation'] ? 'checkbox__error-color' : 'checkbox__active-color'}`}
                                />
                                <label htmlFor="html" className={"panel--font-size"}>Стартап проєкт, який шукає інвестиції</label>
                            </div>
                        </div>
                        { errors['representation'] ? <p className={"panel--error-text"}>{ errors["representation"] }</p> : "" }
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
                                    onChange={(e) => validator.handleChange(e, formData, setFormData, setErrors, validators, errorZeroLengthMessages, errorValidationMessages)}
                                    className={`checkbox ${errors['businessType'] ? 'checkbox__error-color' : 'checkbox__active-color'}`}
                                />
                                <label htmlFor="html" className={"panel--font-size"}>Фізична особа-підприємець</label>
                            </div>
                            <div className={"checkbox--item"}>
                                <input
                                    type="checkbox"
                                    name="businessType.legal"
                                    checked={formData.businessType.legal}
                                    onChange={(e) => validator.handleChange(e, formData, setFormData, setErrors, validators, errorZeroLengthMessages, errorValidationMessages)}
                                    className={`checkbox ${errors['businessType'] ? 'checkbox__error-color' : 'checkbox__active-color'}`}
                                />
                                <label htmlFor="html" className={"panel--font-size"}>Юридична особа</label>
                            </div>
                        </div>
                        { errors['businessType'] ? <p className={"panel--error-text"}>{ errors["businessType"] }</p> : "" }
                    </div>
                    <div>
                        <span className={"panel--font-size"}>Реєструючись, я погоджуюсь з </span>
                        <Link className={"panel--font-size text-underline text-bold"} to={"/policy"}>правилами використання</Link>
                        <span className={"panel--font-size"}> сайту Craftmerge</span>
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
                        Зареєструватися
                    </button>
                </div>
            </div>
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

import './registration.css';
import { Link } from 'react-router-dom';
import { useState } from 'react';

function RegistrationPage() {
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
        confirmPassword: (value, data) => value === data.password,
        firstName: (value) => /^[A-Za-z]{2,}$/.test(value),
        lastName: (value) => /^[A-Za-z]{2,}$/.test(value),
        representation: (value) => Object.values(value).some(v => v),
        businessType: (value) => Object.values(value).some(v => v)
    };

    const [errors, setErrors] = useState({});

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        const realValue = type === "checkbox" ? checked : value;

        if (name.includes(".")) {
            const [group, field] = name.split(".");

            const updatedGroup = {
                ...formData[group],
                [field]: realValue
            };

            setFormData(prev => ({
                ...prev,
                [group]: updatedGroup
            }));

            const error = validateField(group, updatedGroup, {
                ...formData,
                [group]: updatedGroup
            });

            setErrors(prev => {
                const newErrors = { ...prev };
                if (!error) {
                    delete newErrors[group];
                } else {
                    newErrors[group] = error;
                }
                return newErrors;
            });

        } else {
            setFormData(prev => ({ ...prev, [name]: realValue }));

            const error = validateField(name, realValue, {
                ...formData,
                [name]: realValue
            });

            setErrors(prev => {
                const newErrors = { ...prev };
                if (!error) {
                    delete newErrors[name];
                } else {
                    newErrors[name] = error;
                }
                return newErrors;
            });
        }
    };

    const validateField = (key, value, data) => {
        const validator = validators[key];
        if (!validator) return null;

        const isValid = validator.length === 2
            ? validator(value, data)
            : validator(value);

        return isValid ? null : "Invalid value";
    };

    const validate = (data, validators) => {
        const errors = {};

        for (const key in validators) {
            const validator = validators[key];
            const value = data[key];

            const isValid = validator.length === 2
                ? validator(value, data)
                : validator(value);

            if (!isValid) {
                errors[key] = "Invalid value";
            }
        }

        return errors;
    };

    const handleSubmit = () => {
        const validationErrors = validate(formData, validators);
        setErrors(validationErrors);

        if (Object.keys(validationErrors).length === 0) {
            console.log("Ready to go...");
        } else {
            console.log("Errors:", validationErrors);
        }
    };

    return (
        <div className={'registration'}>
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
                            onChange={handleChange}
                            placeholder={'Введіть назву вашої компанії'}
                            className={`input input-text input__width ${errors['companyName'] ? 'input__error-border-color' : ''}`}
                        />
                        { errors['companyName'] ? <p className={"panel--error-text"}>Не ввели назву компанії</p> : "" }
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
                            className={`input input-text input__width ${errors['email'] ? 'input__error-border-color' : ''}`}
                        />
                        { errors['email'] ? <p className={"panel--error-text"}>Не ввели електронну пошту</p> : "" }
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
                        { errors['password'] ? <p className={"panel--error-text"}>Не ввели пароль</p> : "" }
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
                            onChange={handleChange}
                            placeholder={'Введіть пароль ще раз'}
                            className={`input input-text input__width ${errors['confirmPassword'] ? 'input__error-border-color' : ''}`}
                        />
                        { errors['confirmPassword'] ? <p className={"panel--error-text"}>Не ввели пароль ще раз</p> : "" }
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
                            onChange={handleChange}
                            placeholder={'Введіть ваше прізвище'}
                            className={`input input-text input__width ${errors['lastName'] ? 'input__error-border-color' : ''}`}
                        />
                        { errors['lastName'] ? <p className={"panel--error-text"}>Не ввели прізвище</p> : "" }
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
                            onChange={handleChange}
                            placeholder={'Введіть ваше ім’я'}
                            className={`input input-text input__width ${errors['firstName'] ? 'input__error-border-color' : ''}`}
                        />
                        { errors['firstName'] ? <p className={"panel--error-text"}>Не ввели ім’я</p> : "" }
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
                                    onChange={handleChange}
                                    className={`checkbox ${errors['representation'] ? 'checkbox__error-color' : 'checkbox__active-color'}`}
                                />
                                <label htmlFor="html">Зареєстрована компанія</label>
                            </div>
                            <div className={"checkbox--item"}>
                                <input
                                    type="checkbox"
                                    name="representation.startup"
                                    checked={formData.representation.startup}
                                    onChange={handleChange}
                                    className={`checkbox ${errors['representation'] ? 'checkbox__error-color' : 'checkbox__active-color'}`}
                                />
                                <label htmlFor="html">Стартап проєкт, який шукає інвестиції</label>
                            </div>
                        </div>
                        { errors['representation'] ? <p className={"panel--error-text"}>Виберіть кого ви представляєте</p> : "" }
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
                                <label htmlFor="html">Фізична особа-підприємець</label>
                            </div>
                            <div className={"checkbox--item"}>
                                <input
                                    type="checkbox"
                                    name="businessType.legal"
                                    checked={formData.businessType.legal}
                                    onChange={handleChange}
                                    className={`checkbox ${errors['businessType'] ? 'checkbox__error-color' : 'checkbox__active-color'}`}
                                />
                                <label htmlFor="html">Юридична особа</label>
                            </div>
                        </div>
                        { errors['businessType'] ? <p className={"panel--error-text"}>Виберіть який суб’єкт господарювання ви представляєте</p> : "" }
                    </div>
                    <div>
                        <span className={"registration--policy-term"}>Реєструючись, я погоджуюсь з </span>
                        <Link className={"registration--policy-term text-underline text-bold"} to={"/policy"}>правилами використання</Link>
                        <span className={"registration--policy-term"}> сайту Craftmerge</span>
                    </div>
                </div>
                <hr className={'panel--hr'} />
                <button
                    onClick={handleSubmit}
                    className={
                        'button button__padding button__primary-color panel--button'
                    }
                >
                    Зареєструватися
                </button>
            </div>
            <div className={"panel--under-panel"}>
                <span>
                    Ви вже зареєстровані у нас?
                </span>
                <Link className={'text-underline text-bold'} to={'/login'}>
                    Увійти
                </Link>
            </div>
        </div>
    );
}

export default RegistrationPage;

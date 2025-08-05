import './registration.css';
import { Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { Validator } from '../../utils/validation/validate';
import Button from '../../components/Button/button';
import { registerUser } from '../../api';
import Panel, { PanelBody, PanelBodyTitle, PanelNavigation, PanelTitle } from '../../components/Panel/panel';
import TextInput from '../../components/TextInput/textInput';
import Checkbox from '../../components/Checkbox/checkbox';

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
                    <PanelBodyTitle title={'Обов’язкові поля позначені зірочкою'} />
                    <div>
                        <PanelBodyTitle title={'Назва компанії'} className={'content--text-container__margin'} />
                        <TextInput
                            name="companyName"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={formData.companyName}
                            onChange={handleChange}
                            placeholder={'Введіть назву вашої компанії'}
                            className={errors['companyName'] && 'input__error-border-color'}
                        />
                        { errors['companyName'] ? <p className={"panel--danger-text"}>{ errors['companyName'] }</p> : "" }
                    </div>
                    <div>
                        <PanelBodyTitle title={'Електронна пошта'} className={'content--text-container__margin'} />
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
                        { errors['email'] ? <p className={"panel--danger-text"}>{ errors['email'] }</p> : ""}
                    </div>
                    <div>
                        <PanelBodyTitle title={'Пароль'} className={'content--text-container__margin'}>
                            Пароль повинен мати 8+ символів, містити принаймні велику, малу літеру (A..Z, a..z) та цифру (0..9).
                        </PanelBodyTitle>
                        <TextInput
                            name="password"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={formData.password}
                            onChange={handleChange}
                            placeholder={'Введіть пароль'}
                            className={errors['password'] && 'input__error-border-color'}
                        />
                        { errors['password'] ? <p className={"panel--danger-text"}>{ errors['password'] }</p> : "" }
                    </div>
                    <div>
                        <PanelBodyTitle title={'Повторіть пароль'} className={'content--text-container__margin'} />
                        <TextInput
                            name="confirmPassword"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={formData.confirmPassword}
                            onChange={handleChange}
                            placeholder={'Введіть пароль ще раз'}
                            className={errors['confirmPassword'] && 'input__error-border-color'}
                        />
                        { errors['confirmPassword'] ? <p className={"panel--danger-text"}>{ errors["confirmPassword"] }</p> : "" }
                    </div>
                    <div>
                        <PanelBodyTitle title={'Прізвище'} className={'content--text-container__margin'} />
                        <TextInput
                            name="lastName"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={formData.lastName}
                            onChange={handleChange}
                            placeholder={'Введіть ваше прізвище'}
                            className={errors['lastName'] && 'input__error-border-color'}
                        />
                        { errors['lastName'] ? <p className={"panel--danger-text"}>{ errors["lastName"] }</p> : "" }
                    </div>
                    <div>
                        <PanelBodyTitle title={'Ім‘я'} className={'content--text-container__margin'} />
                        <TextInput
                            name="firstName"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={formData.firstName}
                            onChange={handleChange}
                            placeholder={'Введіть ваше ім’я'}
                            className={errors['firstName'] && 'input__error-border-color'}
                        />
                        { errors['firstName'] ? <p className={"panel--danger-text"}>{ errors["firstName"] }</p> : "" }
                    </div>
                    <div>
                        <PanelBodyTitle title={'Кого ви представляєте?'} className={'content--text-container__margin'} />
                        <Checkbox
                            groupKey={"representation"}
                            values={formData.representation}
                            labels={{
                                company: "Зареєстрована компанія",
                                startup: "Стартап проєкт, який шукає інвестиції"
                            }}
                            errors={errors}
                            handleChange={handleChange}
                        />
                        { errors['representation'] ? <p className={"panel--danger-text"}>{ errors["representation"] }</p> : "" }
                    </div>
                    <div>
                        <PanelBodyTitle title={'Який суб’єкт господарювання ви представляєте?'} className={'content--text-container__margin'} />
                        <Checkbox
                            groupKey={"businessType"}
                            values={formData.businessType}
                            labels={{
                                individual: "Фізична особа-підприємець",
                                legal: "Юридична особа"
                            }}
                            errors={errors}
                            handleChange={handleChange}
                        />
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

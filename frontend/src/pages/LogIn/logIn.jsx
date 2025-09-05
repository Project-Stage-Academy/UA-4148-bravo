import './logIn.css';
import Panel, {
    PanelBody,
    PanelBodyBottomLink,
    PanelBodyTitle,
    PanelNavigation,
    PanelTitle,
} from '../../components/Panel/panel';
import TextInput from '../../components/TextInput/textInput';
import HiddenInput from '../../components/HiddenInput/hiddenInput';
import Button from '../../components/Button/button';
import { Link, useNavigate } from 'react-router-dom';
import { Validator } from '../../utils/validation/validate';
import { useAuthContext } from '../../provider/AuthProvider/authProvider';
import bruteForce from "../../utils/bruteForce/bruteForce";
import { useFormWithProtection } from '../../hooks/useFormWithProtection';
import { useFormWithServerErrors } from '../../hooks/useFormWithServerErrors';

/**
 * LogInPage component
 * @returns {JSX.Element}
 */
function LogInPage() {
    const { login } = useAuthContext();

    // Hook to navigate programmatically
    const navigate = useNavigate();

    // Brute force max attempts constant
    const MAX_ATTEMPTS = 5;

    // Form with protection hook
    const form = useFormWithProtection({
        email: "",
        password: "",
        unexpected: "",
    });

    // Function to handle server-side errors
    const extractError = (error) => {
        if (error?.response?.status === 404) {
            return { email: Validator.serverSideErrorMessages.noUserFoundByProvidedData };
        } else {
            return { unexpected: Validator.serverSideErrorMessages.unexpected };
        }
    };

    // Function to handle form submission with brute force protection
    const doSubmit = ({ form, handleError }) => {
        login(form.data.email, form.data.password)
            .then((result) => {
                if (result.newUser.companyId && result.newUser.companyType) {
                    navigate('/');
                } else {
                    navigate('/auth/register/user-represent');
                }
            })
            .catch((error) =>
                bruteForce(error, {
                    attempts: form.attempts,
                    setAttempts: form.setAttempts,
                    setIsLocked: form.setIsLocked,
                    handleError,
                })
            )
            .finally(() => form.setIsLocked(false));
    };

    const { handleSubmit, handleChange } = useFormWithServerErrors({
        form,
        navigate,
        extractError,
        doSubmit,
    });

    return (
        <>
            <Panel aria-labelledby="login-form-title">
                <PanelTitle id="login-form-title">Вхід на платформу</PanelTitle>
                <PanelBody>
                    <div>
                        <PanelBodyTitle
                            id="email-label"
                            title={'Електронна пошта'}
                            className={'content--text-container__margin'}
                            required={false}
                        />
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
                    <div>
                        <PanelBodyTitle
                            id="password-label"
                            title={'Пароль'}
                            className={'content--text-container__margin'}
                            required={false}
                        />
                        <HiddenInput
                            id="password"
                            name="password"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={form.data.password}
                            onChange={handleChange}
                            placeholder={'Введіть пароль'}
                            className={
                                form.errors['password'] && 'input__error-border-color'
                            }
                            aria-labelledby="password-label"
                            aria-describedby={form.errors['password'] ? 'password-error' : undefined}
                            aria-invalid={!!form.errors['password']}
                            aria-required="true"
                        />
                        {form.errors['password'] && (
                            <p id="password-error"
                               className={'panel--danger-text'}
                               role="alert"
                            >
                                {form.errors['password']}
                            </p>
                        )}
                        <PanelBodyBottomLink
                            linkText="Забули пароль?"
                            to="/auth/forgot"
                        />
                    </div>
                    {!form.isLocked && form.attempts >= (MAX_ATTEMPTS - 2 - 1) && (
                        <p className={'content--text'}
                           role="alert"
                        >
                            Залишилося спроб: {MAX_ATTEMPTS - form.attempts}
                        </p>
                    )}
                    {form.isLocked && form.attempts >= (MAX_ATTEMPTS + 1 - 1) && (
                        <p className={'panel--danger-text'}>
                            Повторіть спробу через 30 секунд
                        </p>
                    )}
                    {form.errors['unexpected'] && (
                        <p className={'panel--danger-text'}>
                            {form.errors['unexpected']}
                        </p>
                    )}
                </PanelBody>
                <PanelNavigation>
                    <Button
                        onClick={handleSubmit}
                        disabled={form.isDisabled || form.isLocked}
                        className={'button__padding panel--button'}
                        type="submit"
                    >
                        Увійти
                    </Button>
                </PanelNavigation>
            </Panel>
            <div className={'panel--under-panel'}>
                <span>Вперше на нашому сайті?</span>
                <Link className={'text-underline text-bold'} to={'/auth/register'}>
                    Зареєструйтесь
                </Link>
            </div>
        </>
    );
}

export default LogInPage;

import { Link, useLocation, useNavigate } from 'react-router-dom';
import Panel, { PanelBody, PanelBodyTitle, PanelNavigation, PanelTitle } from '../../components/Panel/panel';
import Button from '../../components/Button/button';
import { Validator } from '../../utils/validation/validate';
import HiddenInput from '../../components/HiddenInput/hiddenInput';
import { useAuthContext } from '../../provider/AuthProvider/authProvider';
import { useFormWithProtection } from '../../hooks/useFormWithProtection';
import bruteForce from '../../utils/bruteForce/bruteForce';
import { useEffect } from 'react';
import { useFormWithServerErrors } from '../../hooks/useFormWithServerErrors';

/**
 * RestorePassword component handles the user password restoration process.
 * It allows users to set a new password and confirm it.
 * It validates the input and displays any errors that occur during the process.
 * If the password is successfully restored, it navigates to a confirmation page.
 * If there are validation errors or server-side errors, it displays appropriate messages.
 * @returns {JSX.Element}
 */
function RestorePassword() {
    const { confirmReset } = useAuthContext();

    // Hook to navigate programmatically
    const navigate = useNavigate();

    // Form with protection hook
    const form = useFormWithProtection({
        password: "",
        confirmPassword: "",
        unexpected: "",
    });

    const location = useLocation();

    useEffect(() => {
        const { user_id, token } = location.state || {};
        if (!user_id || !token) navigate('/404');
    }, [location.state, navigate]);

    // Function to handle server-side errors
    const extractError = (error) => {
        return { unexpected: Validator.serverSideErrorMessages.unexpected };
    };

    // Function to handle form submission with brute force protection
    const doSubmit = ({ form, handleError }) => {
        confirmReset(location.state.user_id, location.state.token, form.data.password)
            .then(() => navigate('/auth/restore-password/done'))
            .catch((error) => bruteForce(error, {
                attempts: form.attempts,
                setAttempts: form.setAttempts,
                setIsLocked: form.setIsLocked,
                handleError
            }))
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
            <Panel aria-labelledby="restore-password-form-title">
                <PanelTitle id="restore-password-form-title">Відновлення паролю</PanelTitle>
                <PanelBody>
                    <div>
                        <PanelBodyTitle
                            id="restore-password-label"
                            title={'Пароль'}
                            className={'content--text-container__margin'}
                            required={false}
                        >
                            Пароль повинен мати 8+ символів, містити принаймні велику, малу літеру (A..Z, a..z) та цифру (0..9).
                        </PanelBodyTitle>
                        <HiddenInput
                            name="password"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={form.data.password}
                            onChange={handleChange}
                            className={form.errors['password'] ? 'input__error-border-color' : ''}
                            aria-labelledby="restore-password-label"
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
                    </div>
                    <div>
                        <PanelBodyTitle
                            id="confirm-password-label"
                            title={'Повторіть пароль'}
                            className={'content--text-container__margin'}
                            required={false}
                        />
                        <HiddenInput
                            id="confirmPassword"
                            name="confirmPassword"
                            autoComplete="off"
                            autoCorrect="off"
                            spellCheck="false"
                            value={form.data.confirmPassword}
                            onChange={handleChange}
                            className={form.errors['confirmPassword'] ? 'input__error-border-color' : ''}
                            aria-labelledby="confirm-password-label"
                            aria-describedby={form.errors['confirmPassword'] ? 'confirm-password-error' : undefined}
                            aria-invalid={!!form.errors['confirmPassword']}
                            aria-required="true"
                        />
                        {form.errors['confirmPassword'] && (
                            <p id="confirm-password-error"
                               className={'panel--danger-text'}
                               role="alert"
                            >
                                {form.errors['confirmPassword']}
                            </p>
                        )}
                    </div>
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
                        type="button"
                    >
                        Зберегти пароль
                    </Button>
                </PanelNavigation>
            </Panel>
            <div className={"panel--under-panel"}>
                <Link className={'text-underline text-bold'} to={'/'}>
                    Повернутися до входу
                </Link>
            </div>
        </>
    );
}

export default RestorePassword;

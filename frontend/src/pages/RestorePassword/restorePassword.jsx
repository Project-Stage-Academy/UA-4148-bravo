import { Link, useLocation } from 'react-router-dom';
import Panel, { PanelBody, PanelBodyTitle, PanelNavigation, PanelTitle } from '../../components/Panel/panel';
import Button from '../../components/Button/button';
import { Validator } from '../../utils/validation/validate';
import HiddenInput from '../../components/HiddenInput/hiddenInput';
import { useAuthContext } from '../../provider/AuthProvider/authProvider';
import { useFormWithProtection } from '../../hooks/useFormWithProtection/useFormWithProtection';
import bruteForce from '../../utils/bruteForce/bruteForce';
import { useEffect } from 'react';

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

    // Form with protection hook
    const {
        formData, setFormData,
        errors, setErrors,
        attempts, setAttempts,
        isLocked, setIsLocked,
        isDisabled, navigate,
    } = useFormWithProtection({
        password: "",
        confirmPassword: "",
        unexpected: "",
    });

    const location = useLocation();

    useEffect(() => {
        if (!location.state) console.log("state is empty");
        else {
            if (!location.state.user_id) console.log("user_id is missing");
            if (!location.state.token) console.log("token is missing");
        }
        if (!location.state
            ||!location.state.user_id
            || !location.state.token
        ) navigate('/404');
    }, [location.state, navigate]);

    // Function to handle server-side errors
    const handleError = () => {
        setErrors(prev => ({
            ...prev,
            unexpected: Validator.serverSideErrorMessages.unexpected
        }));
    };

    // Function to handle form submission
    const handleSubmit = () => {
        if (isLocked) return;
        setIsLocked(true);

        const validationErrors = Validator.validate(
            formData
        );
        setErrors(validationErrors);

        if (Object.values(validationErrors).every(value => value === null)) {
            confirmReset(location.state.user_id, location.state.token,formData.password)
                .then(() => navigate('/auth/restore-password/done'))
                .catch((error) => bruteForce(error, {
                    attempts,
                    setAttempts,
                    setIsLocked,
                    handleError
                }));
        } else {
            console.log('Errors:', validationErrors);
        }
        setIsLocked(false);
    };

    // Function to handle input changes
    const handleChange = (e) => {
        Validator.handleChange(e, formData, setFormData, setErrors);
    };

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
                            value={formData.password}
                            onChange={handleChange}
                            className={errors['password'] && 'input__error-border-color'}
                            aria-labelledby="restore-password-label"
                            aria-describedby={errors['password'] ? 'password-error' : undefined}
                            aria-invalid={!!errors['password']}
                            aria-required="true"
                        />
                        {errors['password'] && (
                            <p id="password-error"
                               className={'panel--danger-text'}
                               role="alert"
                            >
                                {errors['password']}
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
                            value={formData.confirmPassword}
                            onChange={handleChange}
                            className={errors['confirmPassword'] && 'input__error-border-color'}
                            aria-labelledby="confirm-password-label"
                            aria-describedby={errors['confirmPassword'] ? 'confirm-password-error' : undefined}
                            aria-invalid={!!errors['confirmPassword']}
                            aria-required="true"
                        />
                        {errors['confirmPassword'] && (
                            <p id="confirm-password-error"
                               className={'panel--danger-text'}
                               role="alert"
                            >
                                {errors['confirmPassword']}
                            </p>
                        )}
                    </div>
                    { errors['unexpected'] && <p className={"panel--danger-text"}>{ errors['unexpected'] }</p>}
                </PanelBody>
                <PanelNavigation>
                    <Button
                        onClick={handleSubmit}
                        disabled={isDisabled || isLocked}
                        className={'button__padding panel--button'}
                        type="submit"
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

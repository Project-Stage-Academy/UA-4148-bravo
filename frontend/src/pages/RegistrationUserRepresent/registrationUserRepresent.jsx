import Panel, {
    PanelBody,
    PanelBodyTitle,
    PanelNavigation,
    PanelTitle,
} from '../../components/Panel/panel';
import Button from '../../components/Button/button';
import Checkbox from '../../components/Checkbox/checkbox';
import TextInput from '../../components/TextInput/textInput';
import { Validator } from '../../utils/validation/validate';
import { useAuthContext } from '../../provider/AuthProvider/authProvider';
import { useFormWithProtection } from '../../hooks/useFormWithProtection';
import { useFormWithServerErrors } from '../../hooks/useFormWithServerErrors';
import { useNavigate } from 'react-router-dom';
import bruteForce from '../../utils/bruteForce/bruteForce';

/**
 * Registration page that asks the user to select
 * who they represent: Company or Startup project
 *
 * @component
 *
 * @returns {JSX.Element}
 */
function RegistrationUserRepresent() {
    const { bindCompanyToUser } = useAuthContext();

    // Hook to navigate programmatically
    const navigate = useNavigate();

    // Brute force max attempts constant
    const MAX_ATTEMPTS = 5;

    // Form with protection hook
    const form = useFormWithProtection({
        companyName: "",
        representation: {
            company: false,
            startup: false
        },
        unexpected: "",
    });

    // Function to handle server-side errors
    const extractError = (error) => {
        if (error.response.status === 400) {
            return { email: Validator.serverSideErrorMessages.userAlreadyBound };
        } else {
            return { unexpected: Validator.serverSideErrorMessages.unexpected };
        }
    };

    // Function to handle form submission with brute force protection
    const doSubmit = ({ form, handleError }) => {
        bindCompanyToUser(form.data.companyName, form.data.representation.company ? 'investor' : 'startup')
            .then(() => {
                navigate('/auth/register/completed');
            })
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
        <Panel aria-labelledby="registrationUserRepresent-title"
               className={"panel__margin-large"}
        >
            <PanelTitle id="registrationUserRepresent-title">Залишилось декілька кроків</PanelTitle>
            <PanelBody>
                <div>
                    <PanelBodyTitle id="companyName-label"
                                    title={'Назва компанії'}
                                    className={'content--text-container__margin'}
                    />
                    <TextInput
                        id="companyName"
                        name="companyName"
                        autoComplete="off"
                        autoCorrect="off"
                        spellCheck="false"
                        value={form.data.companyName}
                        onChange={handleChange}
                        placeholder={'Введіть назву вашої компанії'}
                        className={form.errors['companyName'] && 'input__error-border-color'}
                        aria-labelledby="companyName-label"
                        aria-describedby={form.errors['companyName'] ? 'companyName-error' : undefined}
                        aria-invalid={!!form.errors['companyName']}
                        aria-required="true"
                    />
                    { form.errors['companyName'] && (
                        <p id="companyName-error"
                           className={'panel--danger-text'}
                           role="alert"
                        >
                            {form.errors['companyName']}
                        </p>
                    )}
                </div>
                <div>
                    <PanelBodyTitle
                        id="representation-title"
                        title={'Кого ви представляєте?'}
                        className={'content--text-container__margin'}
                    />
                    <Checkbox
                        groupKey={"representation"}
                        values={form.data.representation}
                        labels={{
                            company: "Зареєстрована компанія",
                            startup: "Стартап проєкт, який шукає інвестиції"
                        }}
                        errors={form.errors}
                        handleChange={handleChange}
                        isGrouped={true}
                        aria-labelledby="representation-label"
                        aria-describedby={form.errors['representation'] ? 'representation-error' : undefined}
                        aria-invalid={!!form.errors['representation']}
                        aria-required="true"
                    />
                    {form.errors['representation'] && (
                        <p id="representation-error"
                           className={'panel--danger-text'}
                           role="alert"
                        >
                            {form.errors['representation']}
                        </p>
                    )}
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
                { form.errors['unexpected'] && (
                    <p id="unexpected-error"
                       className={"panel--danger-text"}
                       role="alert"
                    >
                        { form.errors['unexpected'] }
                    </p>)
                }
            </PanelBody>
            <PanelNavigation>
                <Button
                    onClick={handleSubmit}
                    className={'button__padding panel--button'}
                    disabled={form.isDisabled || form.isLocked}
                    type="submit"
                >
                    Продовжити
                </Button>
            </PanelNavigation>
        </Panel>
    );
}

export default RegistrationUserRepresent;

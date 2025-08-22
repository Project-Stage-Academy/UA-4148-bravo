import { useNavigate } from 'react-router-dom';
import Panel, {
    PanelBody,
    PanelBodyTitle,
    PanelNavigation,
    PanelTitle,
} from '../../components/Panel/panel';
import Button from '../../components/Button/button';
import Checkbox from '../../components/Checkbox/checkbox';
import TextInput from '../../components/TextInput/textInput';
import { useState } from 'react';
import { Validator } from '../../utils/validation/validate';
import { useAuthContext } from '../../provider/AuthProvider/authProvider';

/**
 * Registration page that asks the user to select
 * who they represent: Company or Startup project
 *
 * @component
 *
 * @returns {JSX.Element}
 */
function RegistrationUserRepresent() {
    // This component handles user registration
    const navigate = useNavigate();

    // Bind user to company
    const { bindCompanyToUser } = useAuthContext();

    // State to hold form data
    const [formData, setFormData] = useState(
        {
            companyName: "",
            representation: {
                company: false,
                startup: false
            },
            unexpected: ""
        });

    // State to hold validation errors
    const [errors, setErrors] = useState({});

    // Function to handle server-side errors
    const handleError = (error) => {
        // TODO
        if (error.response && error.response.status === 401) {
            setErrors(prev => ({
                ...prev,
                companyName: Validator.serverSideErrorMessages.companyAlreadyExist
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
            // TODO
            bindCompanyToUser(formData.companyName, formData.representation.company ? 'investor' : 'startup')
                .then(() => {
                    navigate('/auth/register/completed');
                })
                .catch(handleError);
        } else {
            console.warn('Errors:', validationErrors);
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
                        value={formData.companyName}
                        onChange={handleChange}
                        placeholder={'Введіть назву вашої компанії'}
                        className={errors['companyName'] && 'input__error-border-color'}
                        aria-labelledby="companyName-label"
                        aria-describedby={errors['companyName'] ? 'companyName-error' : undefined}
                        aria-invalid={!!errors['companyName']}
                        aria-required="true"
                    />
                    {errors['companyName'] && (
                        <p id="companyName-error"
                           className={'panel--danger-text'}
                           role="alert"
                        >
                            {errors['companyName']}
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
                        values={formData.representation}
                        labels={{
                            company: "Зареєстрована компанія",
                            startup: "Стартап проєкт, який шукає інвестиції"
                        }}
                        errors={errors}
                        handleChange={handleChange}
                        isGrouped={true}
                        aria-labelledby="representation-label"
                        aria-describedby={errors['representation'] ? 'representation-error' : undefined}
                        aria-invalid={!!errors['representation']}
                        aria-required="true"
                    />
                    {errors['representation'] && (
                        <p id="representation-error"
                           className={'panel--danger-text'}
                           role="alert"
                        >
                            {errors['representation']}
                        </p>
                    )}
                </div>
                { errors['unexpected'] && (
                    <p id="unexpected-error"
                       className={"panel--danger-text"}
                       role="alert"
                    >
                        { errors['unexpected'] }
                    </p>)
                }
            </PanelBody>
            <PanelNavigation>
                <Button
                    onClick={handleSubmit}
                    className={'button__padding panel--button'}
                    type="submit"
                >
                    Продовжити
                </Button>
            </PanelNavigation>
        </Panel>
    );
}

export default RegistrationUserRepresent;

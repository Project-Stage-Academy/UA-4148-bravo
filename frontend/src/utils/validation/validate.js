/**
 * Validator class for form validation.
 * It provides methods to validate individual fields and entire forms,
 * as well as handling changes in form fields.
 */
export class Validator {
    /**
     * Validators for different fields.
     * Each validator is a function that takes a value (and optionally the entire form data)
     * and returns true if the value is valid, or false otherwise.
     * @type {Object<string, function(value: any, data?: Object): boolean>}
     */
    static validators = {
        companyName: (value) => /^\p{L}+(?:[ ’ʼ-]\p{L}+)*$/u.test(value),
        email: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
        password: (value) => /^(?=.*[A-Z])(?=.*\d).{8,}$/.test(value),
        confirmPassword: (value, data) => typeof value === "string" && value.trim() !== "" && value === data.password,
        firstName: (value) => /^[\p{L}’ʼ-]{2,}$/u.test(value),
        lastName: (value) => /^[\p{L}’ʼ-]{2,}$/u.test(value),
        representation: (value) => Object.values(value).some(v => v),
        businessType: (value) => Object.values(value).some(v => v)
    };

    /**
     * Error messages for fields that have zero length.
     * These messages are shown when a field is required but not filled.
     * The keys should match the keys in the `validators` object.
     * @type {Object<string, string>}
     */
    static errorZeroLengthMessages = {
        companyName: "Не ввели назву компанії",
        email: "Не ввели електронну пошту",
        password: "Не ввели пароль",
        confirmPassword: "Не ввели пароль ще раз",
        firstName: "Не ввели ім’я",
        lastName: "Не ввели прізвище",
        representation: "Виберіть кого ви представляєте",
        businessType: "Виберіть який суб’єкт господарювання ви представляєте"
    }

    /**
     * Error messages for fields that do not pass validation.
     * These messages are shown when a field is filled but does not meet the validation criteria.
     * The keys should match the keys in the `validators` object.
     * @type {Object<string, string>}
     */
    static errorValidationMessages = {
        companyName: "Назва компанії не відповідає вимогам",
        email: "Пошта не відповідає вимогам",
        password: "Пароль не відповідає вимогам",
        confirmPassword: "Паролі не співпадають. Будь ласка, введіть однакові паролі в обидва поля",
        firstName: "Ім’я не відповідає вимогам",
        lastName: "Прізвище не відповідає вимогам"
    }

    /**
     * Server-side error messages.
     * These messages are used when the server returns an error during form submission.
     * The keys should match the error codes returned by the server.
     * This is useful for displaying specific error messages based on server responses.
     * For example, if the server indicates that an email already exists,
     * the corresponding message will be shown to the user.
     * This helps in providing a better user experience by informing the user about specific issues.
     * @example
     * // Example usage:
     * const errorCode = "emailAlreadyExist"; // This would be returned by the server
     * const errorMessage = Validator.serverSideErrorMessages[errorCode];
     * console.log(errorMessage); // Outputs: "Ця електронна пошта вже зареєстрована"
     * @type {Object<string, string>}
     */
    static serverSideErrorMessages = {
        emailAlreadyExist: "Ця електронна пошта вже зареєстрована",
        companyAlreadyExist: "Компанія з такою назвою вже зареєстрована",
        noUserFoundByProvidedData: "Облікового запис за вказаними обліковими даними не знайдено",
        emailNotExists: "Зазначена електронна адреса не зареєстрована",
        userAlreadyBound: 'Користувач вже пов’язаний з компанією',
        unexpected: "Сталася непередбачена помилка. Будь ласка, спробуйте ще раз пізніше"
    }

    /**
     * Validates a single field based on its key, value, and the entire form data.
     * It checks if the field is required and has a zero length, and if it passes the validation criteria.
     * If the field is valid, it returns null; otherwise, it returns the corresponding error message.
     * @param key - The key/name of the field to validate.
     * @param value - The value of the field to validate.
     * @param data - The entire form data object, used for validation that requires context from other fields.
     * @param errorZeroLengthMessages - Error messages for fields that have zero length.
     * @param errorValidationMessages - Error messages for fields that do not pass validation.
     * @param validators - An object containing validation functions for each field.
     * @return {string|null} - Returns an error message if the field is invalid, or null if it is valid.
     */
    static validateField(
        key,
        value,
        data,
        errorZeroLengthMessages = Validator.errorZeroLengthMessages,
        errorValidationMessages = Validator.errorValidationMessages,
        validators = Validator.validators
    ) {
        const validator = validators[key];
        if (!validator) return null;
        const errorZeroLengthMessage = errorZeroLengthMessages[key];
        if (!errorZeroLengthMessage) return null;

        if (typeof value === "string" && value.trim() === "")
            return errorZeroLengthMessage;
        else if (typeof value === "object" && !Object.values(data[key]).some(v => v))
            return errorZeroLengthMessage;

        const errorValidationMessage = errorValidationMessages[key];
        if (!errorValidationMessage) return null;

        const isValid = validator.length === 2
            ? validator(value, data)
            : validator(value);

        return isValid ? null : errorValidationMessage;
    }

    /**
     * Validates an entire form by iterating over each field,
     * applying the `validateField` method to each field's value.
     * It returns an object where each key corresponds to a field and its value is either null
     * (if the field is valid) or an error message (if the field is invalid).
     * @param data - The form data object containing all fields to validate.
     * @param errorZeroLengthMessages - Error messages for fields that have zero length.
     * @param errorValidationMessages - Error messages for fields that do not pass validation.
     * @param validators - An object containing validation functions for each field.
     * @returns {Object<string, string|null>} - An object with field names as keys and error messages or null as values.
     */
    static validate(
        data,
        errorZeroLengthMessages = Validator.errorZeroLengthMessages,
        errorValidationMessages = Validator.errorValidationMessages,
        validators = Validator.validators
    ) {
        const errors = {};

        for (const key in data) {
            const value = data[key];
            errors[key] = Validator.validateField(key, value, data, errorZeroLengthMessages, errorValidationMessages, validators);
        }

        return errors;
    }

    /**
     * Handles the change event for form fields.
     * It updates the form data state and validates the field that changed.
     * If the field is part of a group (indicated by a dot in the name),
     * it updates the group and validates the entire group.
     * It also updates the errors state based on the validation results.
     * @param e - The change event object.
     * @param formData - The current form data state.
     * @param setFormData - Function to update the form data state.
     * @param setErrors - Function to update the errors state.
     * @param errorZeroLengthMessages - Error messages for fields that have zero length.
     * @param errorValidationMessages - Error messages for fields that do not pass validation.
     * @param validators - An object containing validation functions for each field.
     * @return {void}
     */
    static handleChange(
        e,
        formData,
        setFormData,
        setErrors,
        errorZeroLengthMessages = Validator.errorZeroLengthMessages,
        errorValidationMessages = Validator.errorValidationMessages,
        validators = Validator.validators
    ) {
        const { name, value, type, checked } = e.target;
        const realValue = type === "checkbox" ? checked : value;

        let argKey, argValue;
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

            argKey = group;
            argValue = updatedGroup;
        } else {
            setFormData(prev => ({ ...prev, [name]: realValue }));

            argKey = name;
            argValue = realValue;
        }

        const error = Validator.validateField(argKey, argValue, {
            ...formData,
            [name]: realValue
        }, errorZeroLengthMessages, errorValidationMessages, validators);

        setErrors(prev => {
            const newErrors = { ...prev };
            if (!error) {
                delete newErrors[name];
            } else {
                newErrors[name] = error;
            }
            return newErrors;
        });
    };
}

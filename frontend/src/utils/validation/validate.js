export class Validator {
    static validators = {
        companyName: (value) => /^[\w\s]{2,}$/.test(value),
        email: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
        password: (value) => /^(?=.*[A-Z])(?=.*\d).{6,}$/.test(value),
        confirmPassword: (value, data) => typeof value === "string" && value.trim() !== "" && value === data.password,
        firstName: (value) => /^[A-Za-z]{2,}$/.test(value),
        lastName: (value) => /^[A-Za-z]{2,}$/.test(value),
        representation: (value) => Object.values(value).some(v => v),
        businessType: (value) => Object.values(value).some(v => v)
    };

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

    static errorValidationMessages = {
        companyName: "Назва компанії не відповідає вимогам",
        email: "Пошта не відповідає вимогам",
        password: "Пароль не відповідає вимогам",
        confirmPassword: "Паролі не співпадають. Будь ласка, введіть однакові паролі в обидва поля",
        firstName: "Ім’я не відповідає вимогам",
        lastName: "Прізвище не відповідає вимогам"
    }

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

            const error = Validator.validateField(group, updatedGroup, {
                ...formData,
                [group]: updatedGroup
            }, errorZeroLengthMessages, errorValidationMessages, validators);

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

            const error = Validator.validateField(name, realValue, {
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
        }
    };
}

export class Validator {
    validateField(key, value, data, validators, errorZeroLengthMessages, errorValidationMessages) {
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

    validate(data, validators, errorZeroLengthMessages, errorValidationMessages) {
        const errors = {};

        for (const key in validators) {
            const value = data[key];
            errors[key] = this.validateField(key, value, data, validators, errorZeroLengthMessages, errorValidationMessages);
        }

        return errors;
    }

    handleChange(e, formData, setFormData, setErrors, validators, errorZeroLengthMessages, errorValidationMessages) {
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

            const error = this.validateField(group, updatedGroup, {
                ...formData,
                [group]: updatedGroup
            }, validators, errorZeroLengthMessages, errorValidationMessages);

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

            const error = this.validateField(name, realValue, {
                ...formData,
                [name]: realValue
            }, validators, errorZeroLengthMessages, errorValidationMessages);

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

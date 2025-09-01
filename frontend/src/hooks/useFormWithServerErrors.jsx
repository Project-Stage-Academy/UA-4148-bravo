import { Validator } from '../utils/validation/validate';

/**
 * Custom hook to manage form state, validation, and server-side errors.
 * @param {Object} form - form state object
 * @param {(function(string): void)} navigate - navigation function
 * @param {(function(Object): Object)} extractError - function to extract errors from server response
 * @param {(function(Object): void)} doSubmit - function to handle form submission
 * @param {function(any, any): void} handleChangeCustom - optional custom change handler
 */
function useFormWithServerErrors({ form, navigate, extractError, doSubmit, handleChangeCustom }) {

    // Function to process server-side errors
    const handleError = (error) => {
        const extracted = extractError(error);
        form.setErrors(prev => ({ ...prev, ...extracted }));
    };

    // Function to validate form data
    const validate = () => {
        const validationErrors = Validator.validate(form.data);
        form.setErrors(validationErrors);
        return Object.values(validationErrors).every(v => v === null);
    };

    // Function to handle form submission
    const handleSubmit = () => {
        if (form.isLocked) return;
        form.setIsLocked(true);
        if (validate()) {
            doSubmit({ form, navigate, handleError });
        }
    };

    // Function to handle input changes
    const handleChange = (e) => {
        if (handleChangeCustom) {
            handleChangeCustom(e, form);
        } else {
            Validator.handleChange(e, form.data, form.setData, form.setErrors);
        }
    };

    return { handleError, handleSubmit, handleChange, validate };
}

useFormWithServerErrors.propTypes = {
    form: Object.isRequired,
    navigate: Function.isRequired,
    extractError: Function.isRequired,
    doSubmit: Function.isRequired,
    handleChangeCustom: Function,
}

export { useFormWithServerErrors }

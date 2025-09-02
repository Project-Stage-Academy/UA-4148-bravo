import { useState, useMemo } from "react";
import { isFormDisabled } from '../utils/formUtils/isFormDisabled';

/**
 * Hook to manage form state with brute force protection
 * @param initialData - initial form data
 */
function useFormWithProtection(initialData = {}) {
    // Brute force protection
    const [attempts, setAttempts] = useState(0);
    const [isLocked, setIsLocked] = useState(false);

    // State to hold validation errors
    const [errors, setErrors] = useState({});

    // State to hold form data
    const [data, setData] = useState(initialData);

    // Filter out unexpected field from form entries and errors
    const filteredFormEntries = Object.entries(data).filter(
        ([key]) => key !== "unexpected"
    );

    // Filter out unexpected field from error keys
    const filteredErrorKeys = Object.keys(errors).filter(
        (key) => key !== "unexpected"
    );

    // Disabled if form invalid
    const isDisabled = useMemo(() =>
            isFormDisabled(filteredFormEntries, filteredErrorKeys, errors),
        [filteredFormEntries, filteredErrorKeys, errors]
    );

    return {
        attempts,
        setAttempts,
        isLocked,
        setIsLocked,
        errors,
        setErrors,
        data,
        setData,
        isDisabled,
    };
}

useFormWithProtection.propTypes = {
    initialData: Object,
}

export { useFormWithProtection };

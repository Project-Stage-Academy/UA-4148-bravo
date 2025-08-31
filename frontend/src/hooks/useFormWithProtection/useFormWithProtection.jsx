import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";

export function useFormWithProtection(initialData = {}) {
    // Brute force protection
    const [attempts, setAttempts] = useState(0);
    const [isLocked, setIsLocked] = useState(false);

    // Hook to navigate programmatically
    const navigate = useNavigate();

    // State to hold validation errors
    const [errors, setErrors] = useState({});

    // State to hold form data
    const [formData, setFormData] = useState(initialData);

    // Disabled if form invalid
    const isDisabled = useMemo(() => {
        return (
            Object.entries(formData).some(
                ([key, value]) => key !== "unexpected" && !value.trim()
            ) ||
            Object.keys(errors).some(
                (key) => key !== "unexpected" && errors[key]
            )
        );
    }, [formData, errors]);

    return {
        attempts,
        setAttempts,
        isLocked,
        setIsLocked,
        navigate,
        errors,
        setErrors,
        formData,
        setFormData,
        isDisabled,
    };
}

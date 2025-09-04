/**
 * Check if the form should be disabled based on empty fields and errors.
 * @param filteredFormEntries - Filtered form entries
 * @param filteredErrorKeys - Filtered error keys
 * @param errors - Errors
 * @return {boolean}
 */
export function isFormDisabled(filteredFormEntries, filteredErrorKeys, errors) {

    const hasEmptyField = filteredFormEntries.some(
        ([, value]) => {
            switch (typeof value) {
                case 'string':
                    return !value.trim();
                case 'boolean':
                    return value;
                default:
                    return false;
            }
        }
    );

    const hasError = filteredErrorKeys.some(
        (key) => errors[key]
    );

    return hasEmptyField || hasError;
}

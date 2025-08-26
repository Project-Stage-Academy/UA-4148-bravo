import './checkbox.css';
import PropTypes from 'prop-types';
import clsx from 'clsx';

/**
 * Checkbox component to render a group of checkboxes.
 * It accepts a group key, values for each checkbox, error messages, a change handler,
 * and labels for each checkbox.
 * It displays checkboxes with labels and applies styles based on error states.
 * @param groupKey - The key for the group of checkboxes, used to identify the group in the form data.
 * @param values - An object containing the values for each checkbox, where keys are checkbox identifiers and values are booleans indicating whether the checkbox is checked.
 * @param errors - An object containing error messages for the group, where the key is the group key and the value is an error message if applicable.
 * @param handleChange - A function to handle changes to the checkboxes, typically updating the form data state.
 * @param labels - An object containing labels for each checkbox, where keys match the values object and values are the label text to be displayed next to each checkbox.
 * @param isGrouped - If is grouped true then checkbox is now inherits radiobutton and only one checkbox can be selected
 * @returns {JSX.Element}
 */
function Checkbox({ groupKey, values, errors = {}, handleChange, labels, isGrouped }) {
    const handleCheckboxChange = (e) => {
        const { name, checked } = e.target;

        if (isGrouped) {
            const newValues = Object.keys(values).reduce((acc, key) => {
                acc[key] = false;
                return acc;
            }, {});

            newValues[name.split(".")[1]] = checked;
            handleChange({ target: { name: groupKey, value: newValues } });
        } else {
            handleChange(e);
        }
    };

    return (
        <div className={'checkbox--container'}>
            {Object.keys(values).map((key) => (
                <div className="checkbox--item" key={key}>
                    <input
                        type="checkbox"
                        name={`${groupKey}.${key}`}
                        checked={values[key]}
                        onChange={handleCheckboxChange}
                        className={clsx('checkbox', errors[groupKey] ?
                            'checkbox__error-color' :
                            'checkbox__active-color')
                        }
                    />
                    <label className="panel--font-size">{labels[key]}</label>
                </div>
            ))}
        </div>
    );
}

/**
 * Checkbox component to render a group of checkboxes.
 * It accepts a group key, values for each checkbox, error messages, a change handler,
 * and labels for each checkbox.
 * It displays checkboxes with labels and applies styles based on error states.
 * @param groupKey - The key for the group of checkboxes, used to identify the group in the form data.
 * @param values - An object containing the values for each checkbox, where keys are checkbox identifiers and values are booleans indicating whether the checkbox is checked.
 * @param errors - An object containing error messages for the group, where the key is the group key and the value is an error message if applicable.
 * @param handleChange - A function to handle changes to the checkboxes, typically updating the form data state.
 * @param labels - An object containing labels for each checkbox, where keys match the values object and values are the label text to be displayed next to each checkbox.
 */
Checkbox.propTypes = {
    groupKey: PropTypes.string.isRequired,
    values: PropTypes.objectOf(PropTypes.bool).isRequired,
    errors: PropTypes.objectOf(PropTypes.string),
    handleChange: PropTypes.func.isRequired,
    labels: PropTypes.objectOf(PropTypes.string).isRequired,
    isGrouped: PropTypes.bool
};

export default Checkbox;

import './textInput.css';
import PropTypes from 'prop-types';
import clsx from 'clsx';

/**
 * TextInput component to render a styled text input field.
 * It allows customization of attributes such as name, autocomplete, autocorrect,
 * spellcheck, placeholder, value, and onChange handler.
 * It also accepts a className for additional styling.
 * @param name - The name attribute for the input field, used for form submission.
 * @param autoComplete - The autocomplete attribute for the input field, typically set to "off" to disable browser suggestions.
 * @param autoCorrect - The autocorrect attribute for the input field, typically set to "off" to disable autocorrection.
 * @param spellCheck - The spellcheck attribute for the input field, typically set to "false" to disable spell checking.
 * @param placeholder - The placeholder text displayed in the input field when it is empty, providing a hint to the user about what to enter.
 * @param value - The current value of the input field, used to control the input's state.
 * @param onChange - The function to call when the input value changes, typically used to update the state in a parent component.
 * @param className - Additional CSS classes to apply to the input field for custom styling.
 * @returns {JSX.Element}
 */
function TextInput({
                       name='',
                       autoComplete="off",
                       autoCorrect="off",
                       spellCheck="false",
                       placeholder = '',
                       value= '',
                       onChange = () => {},
                       className = ''
               }) {

    return (
        <input
            type="text"
            name={name}
            autoComplete={autoComplete}
            autoCorrect={autoCorrect}
            spellCheck={spellCheck}
            placeholder={placeholder}
            value={value}
            onChange={onChange}
            className={clsx('input', 'input-text', 'input__width', className)}
        />
    );
}

/**
 * PropTypes for TextInput component.
 * This defines the expected types for each prop passed to the TextInput component.
 * It helps in validating the props and ensuring that the component receives the correct data types.
 * @param name - The name attribute for the input field, used for form submission.
 * @param autoComplete - The autocomplete attribute for the input field, typically set to "off" to disable browser suggestions.
 * @param autoCorrect - The autocorrect attribute for the input field, typically set to "off" to disable autocorrection.
 * @param spellCheck - The spellcheck attribute for the input field, typically set to "false" to disable spell checking.
 * @param placeholder - The placeholder text displayed in the input field when it is empty, providing a hint to the user about what to enter.
 * @param value - The current value of the input field, used to control the input's state.
 * @param onChange - The function to call when the input value changes, typically used to update the state in a parent component.
 * @param className - Additional CSS classes to apply to the input field for custom styling.
 */
TextInput.propTypes = {
    name: PropTypes.string,
    autoComplete: PropTypes.string,
    autoCorrect: PropTypes.string,
    spellCheck: PropTypes.string,
    placeholder: PropTypes.string,
    value: PropTypes.string,
    onChange: PropTypes.func,
    className: PropTypes.string
}

export default TextInput;

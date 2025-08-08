import "./button.css";
import PropTypes from 'prop-types';
import clsx from 'clsx';

/**
 * @param {Object} props
 * @param {'primary' | 'secondary' | 'danger' | 'outline'} props.variant - Button variant
 * @param {string} [props.className] - Additional classes
 * @param {React.ReactNode} props.children - Button contents
 */
function Button({  variant = 'primary', className = '', children, ...rest }) {
    return (
        <button className={clsx("button", `button__${variant}-color`, className)} {...rest}>
            {children}
        </button>
    );
}

/**
 * Button component
 * @param {Object} props
 * @param {'primary' | 'secondary' | 'danger' | 'outline'} [props.variant] - Button variant
 * @param {string} [props.className] - Additional classes
 * @param {React.ReactNode} props.children - Button contents
 * @returns {JSX.Element}
 */
Button.propTypes = {
    variant: PropTypes.oneOf(['primary', 'secondary', 'danger', 'outline']),
    className: PropTypes.string,
    children: PropTypes.node.isRequired,
};

export default Button;

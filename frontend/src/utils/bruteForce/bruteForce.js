import PropTypes from 'prop-types';

/**
 * @typedef {Object} BruteForceProps - Represents a bruteForce properties
 * @property {number} attempts - Number of attempts
 * @property {function} setAttempts - Unique identifier for the user
 * @property {function} setIsLocked - First name of the user
 * @property {function} handleError - Last name of the user
 */

/**
 * Brute force
 * @param {Object} error - error message
 * @param {BruteForceProps} props - props
 */
function bruteForce (error, props) {
    props.setAttempts(() => {
        const next = props.attempts + 1;

        if (next >= 5) {
            props.setIsLocked(true);

            setTimeout(() => {
                props.setAttempts(0);
                props.setIsLocked(false);
            }, 30000);
        } else {
            props.handleError(error);
        }

        return next;
    });
}

bruteForce.propTypes = {
    error: PropTypes.object.isRequired,
    props: PropTypes.object.isRequired,
}

export default bruteForce;

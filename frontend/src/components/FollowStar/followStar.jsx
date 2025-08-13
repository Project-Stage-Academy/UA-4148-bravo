import './followStar.css';
import PropTypes from 'prop-types';

/**
 * A component of the “Favorites” button that toggles its state
 * between on and off when clicked.
 *
 * @component
 * @param {Object} props - Properties of the component.
 * @param {boolean} props.value - Current state of the button:
 * `true` - enabled (active icon), `false` - disabled (empty icon).
 * @param {function(boolean): void} props.setter - Function to change the state,
 * usually derived from React useState.
 *
 * @example
 * const [isFavorite, setIsFavorite] = useState(false);
 * return <FollowStar value={isFavorite} setter={setIsFavorite} />;
 */
function FollowStar({ participantId, value, setter }) {
    const handleToggle = () => {
        setter(!value);
    };

    return (
        <button
            key={participantId}
            onClick={handleToggle}
            className={'button button__outline-color'}
        >
            {!value ?
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M17.4266 7.02123C17.3375 6.73827 17.1702 6.48867 16.9454 6.30347C16.7206 6.11826 16.4482 6.00561 16.1622 5.97951L11.9866 5.60519L10.3529 1.57044C10.2406 1.29606 10.0528 1.06203 9.81294 0.897509C9.57312 0.73299 9.29188 0.645264 9.00429 0.645264C8.7167 0.645264 8.43546 0.73299 8.19564 0.897509C7.95582 1.06203 7.76802 1.29606 7.65564 1.57044L6.01983 5.60519L1.84422 5.97951C1.55661 6.00419 1.28244 6.11636 1.05611 6.30195C0.829772 6.48753 0.66136 6.73826 0.572001 7.02268C0.482643 7.3071 0.476317 7.61253 0.553819 7.90066C0.63132 8.18879 0.789197 8.44678 1.00764 8.64226L4.1811 11.5123L3.22877 15.7824C3.16346 16.0732 3.18229 16.3775 3.28291 16.6572C3.38353 16.9369 3.56148 17.1797 3.79451 17.3552C4.02754 17.5307 4.3053 17.6311 4.59308 17.6439C4.88087 17.6566 5.16589 17.5812 5.41254 17.427L9.00209 15.1674L12.5916 17.427C12.8383 17.581 13.1232 17.6562 13.4109 17.6433C13.6985 17.6304 13.9761 17.53 14.209 17.3545C14.4419 17.1791 14.6198 16.9364 14.7204 16.6568C14.821 16.3772 14.8399 16.0731 14.7747 15.7824L13.8224 11.5123L16.9958 8.64226C17.2137 8.44607 17.3708 8.18756 17.4474 7.89917C17.524 7.61078 17.5168 7.30536 17.4266 7.02123ZM12.5367 10.2572C12.3358 10.4384 12.1863 10.6729 12.1044 10.9355C12.0224 11.1981 12.0111 11.4789 12.0715 11.7477L12.9059 15.4924L9.76029 13.5122C9.53186 13.368 9.26955 13.2918 9.00209 13.2918C8.73463 13.2918 8.47233 13.368 8.24389 13.5122L5.09827 15.4924L5.93266 11.7477C5.99312 11.4789 5.98177 11.1981 5.89981 10.9355C5.81784 10.6729 5.66838 10.4384 5.46748 10.2572L2.67715 7.73418L6.35022 7.40466C6.6162 7.38105 6.87083 7.28228 7.08641 7.11908C7.30199 6.95589 7.47024 6.73454 7.57286 6.47911L9.00209 2.94927L10.4313 6.47911C10.5339 6.73454 10.7022 6.95589 10.9178 7.11908C11.1333 7.28228 11.388 7.38105 11.654 7.40466L15.327 7.73418L12.5367 10.2572Z" fill="#80B31E"/>
                </svg>
                :
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M9 14.737L13.1224 17.3458C13.8773 17.824 14.8011 17.1172 14.6025 16.2233L13.5098 11.3174L17.1554 8.01216C17.8209 7.40932 17.4633 6.26599 16.5891 6.19324L11.7913 5.76709L9.91388 1.13143C9.57614 0.289524 8.42386 0.289524 8.08612 1.13143L6.2087 5.75669L1.41085 6.18284C0.536712 6.2556 0.179108 7.39892 0.844648 8.00177L4.49022 11.307L3.39754 16.2129C3.19887 17.1068 4.12268 17.8136 4.87762 17.3355L9 14.737Z" fill="#80B31E"/>
                </svg>
            }
        </button>
    );
}

/**
 * A component of the “Favorites” button that toggles its state
 * between on and off when clicked.
 *
 * @component
 * @property {Object} props - Properties of the component.
 * @property {boolean} props.value - Current state of the button:
 * `true` - enabled (active icon), `false` - disabled (empty icon).
 * @property {function(boolean): void} props.setter - Function to change the state,
 * usually derived from React useState.
 */
FollowStar.propTypes = {
    value: PropTypes.bool,
    setter: PropTypes.func,
}

export default FollowStar;

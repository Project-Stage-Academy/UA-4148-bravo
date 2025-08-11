import './image.css';
import { useState } from 'react';
import PropTypes from 'prop-types';
import clsx from 'clsx';

/**
 * Image component that displays an image with a fallback pattern
 * in case the image fails to load.
 * It uses a state variable to track if the image has encountered an error.
 * If the image fails to load, it displays a fallback pattern instead.
 * @param src - The source URL of the image to display.
 * @param alt - The alt text for the image, used for accessibility.
 * @param className - Additional CSS classes to apply to the image container.
 * @returns {JSX.Element}
 */
function Image({ src, alt, className }) {
    const [hasError, setHasError] = useState(false);

    return (
        <div className={'image-container'}>
            {!hasError && src !== '' && src !== null && src !== undefined ? (
                <img
                    src={src}
                    alt={alt}
                    onError={() => setHasError(true)}
                    className={`main-image ${className || ""}`}
                />
            ) : (
                <div className={clsx('pattern-fallback', className)} />
            )}
        </div>
    );
}

/**
 * Image component that displays an image with a fallback pattern
 * in case the image fails to load.
 * It uses a state variable to track if the image has encountered an error.
 * If the image fails to load, it displays a fallback pattern instead.
 * @param src - The source URL of the image to display.
 * @param alt - The alt text for the image, used for accessibility.
 * @param className - Additional CSS classes to apply to the image container.
 */
Image.propTypes = {
    src: PropTypes.string.isRequired,
    alt: PropTypes.string.isRequired,
    className: PropTypes.string
}

export default Image;

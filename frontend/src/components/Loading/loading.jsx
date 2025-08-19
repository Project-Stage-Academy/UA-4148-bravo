import './loading.css';
import { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import clsx from 'clsx';

/**
 * Loading component that displays a loading animation with dots.
 * The number of dots can be customized via the `quantity` prop.
 * The dots animate in a sequence, creating a loading effect.
 * @param quantity - The number of dots to display in the loading animation.
 * @param className - Additional class style
 * @returns {JSX.Element}
 */
function Loading({ quantity = 4, className }) {
    const [dots, setDots] = useState(Array(quantity).fill(false));

    useEffect(() => {
        let index = 0;

        const interval = setInterval(() => {
            setDots(() => {
                const newDots = Array(quantity).fill(false);
                newDots[index] = true;
                return newDots;
            });

            index = (index + 1) % quantity;
        }, 300);

        return () => clearInterval(interval);
    }, [quantity]);

    return (
        <div className={clsx('loading-container', className)}>
            {dots.map((isActive, i) => (
                <div key={i} className={`loading-dot ${isActive ? 'loading-dot__active' : ''}`}></div>
            ))}
        </div>
    );
}

/**
 * PropTypes for the Loading component.
 * @type {{quantity: number}}
 */
Loading.propTypes = {
    quantity: PropTypes.number,
};

export default Loading;

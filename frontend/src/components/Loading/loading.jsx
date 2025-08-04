import './loading.css';
import { useEffect, useState } from 'react';

/**
 * Loading component that displays a loading animation with dots.
 * The number of dots can be customized via the `quantity` prop.
 * The dots animate in a sequence, creating a loading effect.
 * @param quantity - The number of dots to display in the loading animation.
 * @returns {JSX.Element}
 */
function Loading({ quantity = 4 }) {
    const [dots, setDots] = useState(Array(quantity).fill(false));

    useEffect(() => {
        let index = 0;

        const interval = setInterval(() => {
            setDots(prev => {
                const newDots = Array(quantity).fill(false);
                newDots[index] = true;
                return newDots;
            });

            index = (index + 1) % quantity;
        }, 300);

        return () => clearInterval(interval);
    }, [quantity]);

    return (
        <div className={'loading-container'}>
            {dots.map((isActive, i) => (
                <div key={i} className={`loading-dot ${isActive ? 'loading-dot__active' : ''}`}></div>
            ))}
        </div>
    );
}

export default Loading;

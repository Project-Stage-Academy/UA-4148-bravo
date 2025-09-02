import { useState, useEffect } from "react";
import PropTypes from 'prop-types';

/**
 * Hook to manage mobile state based on window width.
 * @param {number} breakpoint - The width threshold to consider as mobile. Default is 769px.
 * @return {boolean}
 */
function useIsMobile(breakpoint = 769) {
    const [isMobile, setIsMobile] = useState(false);

    useEffect(() => {
        if (typeof window === "undefined") return;

        const handleResize = () => {
            setIsMobile(window.innerWidth <= breakpoint);
        };

        handleResize();

        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, [breakpoint]);

    return isMobile;
}

useIsMobile.propTypes = {
    breakpoint: PropTypes.number,
}

export default useIsMobile;

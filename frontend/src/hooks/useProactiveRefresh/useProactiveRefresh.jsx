import { jwtDecode } from 'jwt-decode';
import { useEffect } from 'react';

function useProactiveRefresh(accessToken, refreshToken) {
    useEffect(() => {
        if (!accessToken || typeof accessToken !== "string") return;

        let isMounted = true;

        (async () => {
            const decoded = jwtDecode(accessToken);
            const exp = decoded.exp * 1000;
            const now = Date.now();

            // 1 min
            const refreshBefore = 60 * 1000;
            const timeout = exp - now - refreshBefore;

            if (timeout > 0) {
                const timerId = setTimeout(() => {
                    if (isMounted) void refreshToken();
                }, timeout);

                return () => {
                    isMounted = false;
                    clearTimeout(timerId);
                };
            } else {
                void refreshToken();
            }
        })();

        return () => {
            isMounted = false;
        };
    }, [accessToken, refreshToken]);
}

export default useProactiveRefresh;

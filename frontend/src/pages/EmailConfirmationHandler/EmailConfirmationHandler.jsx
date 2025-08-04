import { useNavigate, useSearchParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import Loading from '../../components/Loading/loading';
import { confirmUser } from '../../api';

/**
 * Email confirmation handler
 * Display loading while processing information
 * Navigate to done if token is fine
 * Else navigate to error
 * @returns {JSX.Element}
 * @constructor
 */
function EmailConfirmationHandler() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const [status, setStatus] = useState('processing');

    useEffect(() => {
        const token = searchParams.get('token');

        if (token) {
            confirmUser(token)
                .then(() => setStatus('success'))
                .catch(() => setStatus('error'));
        } else {
            setStatus('error');
        }
    }, [searchParams]);

    if (status === 'processing') return <Loading />;
    else if (status === 'success') navigate('/auth/register/done');
    else navigate('/auth/register/error');
}

export default EmailConfirmationHandler;

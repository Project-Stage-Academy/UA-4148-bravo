import './emailConfirmationHandler.css';
import {useNavigate, useParams} from 'react-router-dom';
import { useEffect, useRef, useState } from 'react';
import Loading from '../../components/Loading/loading';
import { useAuthContext } from '../../provider/AuthProvider/authProvider';

/**
 * Email confirmation handler
 * Display loading while processing information
 * Navigate to done if token is fine
 * Else navigate to error
 *
 * @component
 *
 * @returns {JSX.Element}
 */
function EmailConfirmationHandler() {
    const { user_id, token } = useParams();
    const navigate = useNavigate();
    const [status, setStatus] = useState('processing');
    const { confirmEmail } = useAuthContext();

    const didRun = useRef(false);
    useEffect(() => {
        if (didRun.current) return;
        didRun.current = true;

        if (token) {
            const id = Number(user_id);
            if (isNaN(id)) {
                setStatus("error");
            } else {
                confirmEmail(id, token)
                    .then(() => setStatus('success'))
                    .catch(() => setStatus('error'));
            }
        } else {
            setStatus('error');
        }
    }, [user_id, token, confirmEmail]);

    useEffect(() => {
        if (status === 'success') {
            navigate('/auth/register/user-confirmed');
        } else if (status === 'error') {
            navigate('/auth/register/error');
        }
    }, [status, navigate]);

    if (status === 'processing') {
        return <Loading className={'email-confirmation-handler__loading'}/>;
    }
    
    return null;
}

export default EmailConfirmationHandler;

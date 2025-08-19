import './emailConfirmationHandler.css';
import {useNavigate, useParams} from 'react-router-dom';
import { useEffect, useState } from 'react';
import Loading from '../../components/Loading/loading';
import { useAuthContext } from '../../provider/AuthProvider/authProvider';

/**
 * Email confirmation handler
 * Display loading while processing information
 * Navigate to done if token is fine
 * Else navigate to error
 * @returns {JSX.Element}
 */
function EmailConfirmationHandler() {
    const { user_id, token } = useParams();
    const navigate = useNavigate();
    const [status, setStatus] = useState('processing');
    const { confirmEmail } = useAuthContext();

    useEffect(() => {
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
    }, [user_id, token]);

    if (status === 'processing') return <Loading className={'email-confirmation-handler'}/>;
    else if (status === 'success') navigate('/auth/register/done');
    else navigate('/auth/register/error');
}

export default EmailConfirmationHandler;

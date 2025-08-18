import './emailConfirmationHandler.css';
import {useNavigate, useParams} from 'react-router-dom';
import { useEffect, useState } from 'react';
import Loading from '../../components/Loading/loading';

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
    //const {  } = useAuthContext();

    useEffect(() => {
        if (token) {
            // confirmUser(token)
            //     .then(() => setStatus('success'))
            //     .catch(() => setStatus('error'));
        } else {
            setStatus('error');
        }
    }, [user_id, token]);

    if (status === 'processing') return <Loading className={'email-confirmation-handler'}/>;
    else if (status === 'success') navigate('/auth/register/done');
    else navigate('/auth/register/error');
}

export default EmailConfirmationHandler;

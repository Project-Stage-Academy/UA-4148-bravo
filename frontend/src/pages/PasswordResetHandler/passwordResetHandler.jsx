import { useNavigate, useParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import Loading from '../../components/Loading/loading';

function PasswordResetHandler() {
    const { user_id, token } = useParams();
    const navigate = useNavigate();
    const [status, setStatus] = useState('processing');

    useEffect(() => {
        if (!user_id || !token) setStatus('error');
        else setStatus('success');
    }, [user_id, token]);

    useEffect(() => {
        if (status === 'success') {
            navigate('/auth/restore-password', {state: {user_id, token}});
        } else if (status === 'error') {
            navigate('/404');
        }
    }, [status, navigate, user_id, token]);

    if (status === 'processing') {
        return <Loading className={'email-confirmation-handler'}/>;
    }

    return null;
}

export default PasswordResetHandler;

import './passwordResetHandler.css';
import { useNavigate, useParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import Loading from '../../components/Loading/loading';

/**
 * PasswordResetHandler component processes the password reset link.
 * @component
 * @return {JSX.Element|null}
 */
function PasswordResetHandler() {
    const { user_id, token } = useParams();
    const navigate = useNavigate();
    const [status, setStatus] = useState('processing');

    useEffect(() => {
        if (!user_id || !token) return setStatus('error');
        setStatus('success');
    }, [user_id, token]);

    useEffect(() => {
        if (status === 'success') {
            navigate('/auth/restore-password', { state: {user_id, token}, replace: true });
        } else if (status === 'error') {
            navigate('/404');
        }
    }, [status, navigate, user_id, token]);

    if (status === 'processing') {
        return <Loading className={'password-reset-handler__loading'}/>;
    }

    return null;
}

export default PasswordResetHandler;

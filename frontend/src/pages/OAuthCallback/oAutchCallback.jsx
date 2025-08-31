import Loading from '../../components/Loading/loading';
import { useEffect, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { loginOAuth } from '../../api/oauthService';

function OAuthCallback() {
    const { provider } = useParams();
    const location = useLocation();
    const params = new URLSearchParams(location.search);
    const code = params.get('code');
    const [status, setStatus] = useState('processing');
    const navigate = useNavigate();

    useEffect(() => {
        if (provider !== 'google' && provider !== 'github') {
            setStatus('error');
            return;
        }

        if (!code) {
            setStatus('error');
            return;
        }

        setStatus('success');
    }, [provider, code]);

    useEffect(() => {
        if (status === 'success') {
            loginOAuth(provider, code)
                .then(() => {
                    navigate('/');
                })
                .catch(() => setStatus('error'));
        } else if (status === 'error') {
            navigate('/404');
        }
    }, [status, navigate]);

    if (status === 'processing') {
        return <Loading className={'email-confirmation-handler'}/>;
    }

    return null;
}

export default OAuthCallback;

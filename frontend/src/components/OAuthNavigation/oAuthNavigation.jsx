import './oAuthNavigation.css';
import clsx from 'clsx';
import Button from '../Button/button';
import { OAuthGithub, OAuthGoogle } from '../../api/oauthService';

function OAuthNavigation({ className }) {
    return (
        <div className={clsx('oauth__panel', className)}>
            <Button
                variant={'secondary'}
                className={'oauth__btn'}
                onClick={OAuthGoogle}
            >
                <img
                    src="/pictures/svg/oauth_google.svg"
                    alt="Google"
                    className="oauth-icon"
                />
            </Button>
            <Button
                variant={'secondary'}
                className={'oauth__btn'}
                onClick={OAuthGithub}
            >
                <img
                    src="/pictures/svg/oauth_github.svg"
                    alt="Github"
                    className="oauth-icon"
                />
            </Button>
        </div>
    );
}

export default OAuthNavigation;

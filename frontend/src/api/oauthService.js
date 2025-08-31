import { api } from './client';

const GOOGLE_OAUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth';

export async function OAuthGoogle() {
    const params = new URLSearchParams({
        client_id: process.env.REACT_APP_GOOGLE_CLIENT_ID,
        redirect_uri: process.env.REACT_APP_URL + '/oauth/callback/google',
        response_type: 'code',
        scope: 'email profile',
        access_type: 'offline',
        prompt: 'consent',
    });

    window.location.href = `${GOOGLE_OAUTH_URL}?${params.toString()}`;
}

const GITHUB_OAUTH_URL = 'https://github.com/login/oauth/authorize';

export function OAuthGithub() {
    const params = new URLSearchParams({
        client_id: process.env.REACT_APP_GITHUB_CLIENT_ID,
        redirect_uri: process.env.REACT_APP_URL + '/oauth/callback/github',
        scope: 'read:user user:email',
        allow_signup: 'true',
    });

    window.location.href = `${GITHUB_OAUTH_URL}?${params.toString()}`;
}

/**
 * Authenticate users using Google or GitHub OAuth providers.
 * The endpoint exchanges OAuth provider tokens for application
 * JWT tokens and returns user information.
 * @param {'google'||'github'} provider
 * @param {string} token
 * @return {Promise<void>}
 */
export async function loginOAuth(provider, token) {
    await api.post("api/v1/auth/oauth/login/", {
        provider,
        token,
    });
}

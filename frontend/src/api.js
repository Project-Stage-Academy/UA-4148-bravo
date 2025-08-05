import axios from 'axios';

/**
 * API instance for making HTTP requests.
 * This instance is configured to communicate with the backend API.
 * The base URL is set to the backend server's API endpoint.
 * The headers specify that the content type is JSON.
 * @type {axios.AxiosInstance}
 */
const API = axios.create({
    baseURL: 'http://localhost:8000/api',
    headers: {
        'Content-Type': 'application/json'
    }
});

/**
 * Registration API calls
 *
 * Step 1: Register a new user
 * Step 2: Confirm the user registration
 */

/**
 * Registers a new user.
 * @param data - The user data to register.
 * @returns {Promise<axios.AxiosResponse<any>>}
 */
export const registerUser = (data) => API.post('/register', data);

/**
 * Confirms the user registration.
 * This is typically called after the user has received a confirmation email.
 * @param data - The confirmation data, usually containing the user's email and confirmation code.
 * @returns {Promise<axios.AxiosResponse<any>>}
 */
export const confirmUser = (data) => API.post('/confirm-email', { data });

/**
 * Logs in a user.
 * @param data - The login credentials, typically containing email and password.
 * @returns {Promise<axios.AxiosResponse<any>>}
 */
export const loginUser = (data) => API.post('/login', data);

/**
 * Sends a password reset request.
 * This is typically called when the user forgets their password.
 * @param data - The email of the user requesting the password reset.
 * @returns {Promise<axios.AxiosResponse<any>>}
 */
export const restorePassword = (data) => API.post('/restore-password', data);

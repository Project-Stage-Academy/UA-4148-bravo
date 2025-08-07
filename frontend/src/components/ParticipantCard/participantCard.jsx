import './participantCard.css';
import Image from '../Image/image';
import { Link, useNavigate } from 'react-router-dom';
import Button from '../Button/button';
import { useState } from 'react';
import { useAuth } from '../../context/AuthContext/authContext';
import FollowStar from '../FollowStar/followStar';
import PropTypes from 'prop-types';

/**
 * ParticipantCard component
 *
 * Displays a participant/company card with a background image, profile picture,
 * title, location, and optional follow button. Can also show a "recently updated"
 * badge if applicable. Clicking on the background, profile picture, or title
 * navigates to the participant's company profile page.
 *
 * @component
 * @param {Object} props - Component props.
 * @param {string} props.bcgImgSrc - URL of the background image.
 * @param {string} props.ppImgSrc - URL of the profile picture.
 * @param {string} props.alt - Alt text for images.
 * @param {string} props.title - Name/title of the participant.
 * @param {string} props.location - Location of the participant.
 * @param {string|number} props.uid - Unique ID for building the company profile link.
 * @param {string} [props.className] - Additional CSS classes for the card container.
 * @param {boolean} [props.recentlyUpdated] - Whether the participant was recently updated.
 *
 * @example
 * <ParticipantCard
 *   bcgImgSrc="/images/bg.jpg"
 *   ppImgSrc="/images/profile.jpg"
 *   alt="Company name"
 *   title="My Company"
 *   location="New York"
 *   uid="12345"
 *   recentlyUpdated={true}
 * />
 */
function ParticipantCard({bcgImgSrc, ppImgSrc, alt, title, location, uid, className, recentlyUpdated}) {
    const { user } = useAuth();
    const [isFollowed, setFollow] = useState(false);
    const [isRecentlyUpdated] = useState(!!recentlyUpdated);
    const navigate = useNavigate();
    const [companyLink] = useState(`/profile/company/${uid}`);

    return (
        <div className={`participant-card ${className || ''}`}>
            <Link to={companyLink} className={'participant-card--background'}>
                <Image
                    src={bcgImgSrc}
                    alt={alt}
                    className={'participant-card--background-image'}
                />
                {isRecentlyUpdated && <p className={'participant-card--updated'}>Оновлено</p>}
            </Link>
            <Link to={companyLink} className={'participant-card--picture'}>
                <Image
                    src={ppImgSrc}
                    alt={alt}
                    className={'participant-card--picture-image'}
                />
            </Link>
            <div className={'participant-card--info'}>
                <div className={'participant-card--other-services'}>
                    <Link to={companyLink}>
                        <span>Інші послуги</span>
                    </Link>
                </div>
                <div className={'participant-card--text-container'}>
                    <h3 className={'participant-card--title'}>
                        <Link to={companyLink}>
                            <span>{title}</span>
                        </Link>
                    </h3>
                    <p className={'participant-card--location'}>{location}</p>
                </div>
                <div className={'participant-card--nav-menu'}>
                    <div>
                        <Button
                            className={'participant-card--services-btn'}
                            onClick={() => navigate(companyLink)}
                        >
                            Послуги
                        </Button>
                    </div>
                    {user && (
                        <FollowStar value={isFollowed} setter={setFollow} />
                    )}
                </div>
            </div>
        </div>
    );
}

ParticipantCard.propTypes = {
    bcgImgSrc: PropTypes.string.isRequired,
    ppImgSrc: PropTypes.string.isRequired,
    alt: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
    location: PropTypes.string.isRequired,
    uid: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    className: PropTypes.string,
    recentlyUpdated: PropTypes.bool
};

export default ParticipantCard;

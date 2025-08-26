import './participantCard.css';
import Image from '../Image/image';
import { Link, useNavigate } from 'react-router-dom';
import Button from '../Button/button';
import { useState } from 'react';
import { useAuthContext } from '../../provider/AuthProvider/authProvider';
import FollowStar from '../FollowStar/followStar';
import PropTypes from 'prop-types';
import clsx from 'clsx';

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
 * @param {boolean} [props.followed] - Whether the user has kept the card.
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
 *   followed={true}
 *   recentlyUpdated={true}
 * />
 */
function ParticipantCard({bcgImgSrc, ppImgSrc, alt, title, location, uid, className, followed, recentlyUpdated}) {
    const { user } = useAuthContext();
    const [isFollowed, setFollow] = useState(!!followed);
    const navigate = useNavigate();
    const isRecentlyUpdated = !!recentlyUpdated;
    const companyLink = `/profile/company/${uid}`;

    return (
        <div className={clsx('participant-card', className)}>
            <Link to={companyLink} className={'participant-card--background'} tabIndex={-1}>
                <Image
                    src={bcgImgSrc}
                    alt={alt}
                    className={'participant-card--background-image'}
                />
                {isRecentlyUpdated && <p className={'participant-card--updated'}>Оновлено</p>}
            </Link>
            <Link to={companyLink} className={'participant-card--picture'} tabIndex={-1}>
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
                    <p className={'participant-card--location'}>{location && "Локація не знайдена"}</p>
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
                        <FollowStar participantId={uid} value={isFollowed} setter={setFollow} />
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
    followed: PropTypes.bool,
    recentlyUpdated: PropTypes.bool
};

export default ParticipantCard;

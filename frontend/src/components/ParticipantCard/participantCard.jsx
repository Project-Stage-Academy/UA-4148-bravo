import './participantCard.css';
import Image from '../Image/image';
import { Link, useNavigate } from 'react-router-dom';
import Button from '../Button/button';
import { useState } from 'react';
import { useAuth } from '../../context/AuthContext/authContext';
import FollowStar from '../FollowStar/followStar';

function ParticipantCard({bcgImgSrc, ppImgSrc, alt, title, location, uid, className, recentlyUpdated}) {
    const { user } = useAuth();
    const [isFollowed, setFollow] = useState(false);
    const [isRecentlyUpdated] = useState(!!recentlyUpdated);
    const navigate = useNavigate();
    const [companyLink] = useState(`/profile/company/${uid}`);

    return (
        <div className={`participant-card ${className}`}>
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

export default ParticipantCard;

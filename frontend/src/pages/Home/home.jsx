import './home.css';
import Button from '../../components/Button/button';
import { Link } from 'react-router-dom';
import ParticipantCard from '../../components/ParticipantCard/participantCard';
import { useEffect, useState } from 'react';
import PropTypes from 'prop-types';

/**
 * NewParticipantGrid component
 * Renders a grid of new participants
 * Each participant includes a background image, profile picture, title, and location
 * The component maps over the provided data and renders a ParticipantCard for each item
 * @param {Array.<Object>} data - Array of objects containing participant data
 * @returns {JSX.Element}
 */
function NewParticipantGrid({ data }) {
    return (
        <div className={'participants--grid'}>
            {data?.map((item, index) => (
                <ParticipantCard key={index} className={'participants--grid-item'} uid={item.uid} bcgImgSrc={item.bcgImgSrc} ppImgSrc={item.ppImgSrc} alt={item.alt} title={item.title} location={item.location} />
            ))}
        </div>
    );
}

/**
 * NewParticipantGrid component prop types
 * Renders a grid of new participants
 * Each participant includes a background image, profile picture, title, and location
 * The component maps over the provided data and renders a ParticipantCard for each item
 * @property {Array.<Object>} data - Array of objects containing participant data
 */
NewParticipantGrid.propTypes = {
    data: PropTypes.arrayOf(PropTypes.object).isRequired
}

/**
 * TargetAudienceGrid component
 * Renders a grid of target audience items
 * Each item includes an image and a title
 * @param {Array.<Object>} data - Array of objects containing imgSrc, alt, and title for each target audience item
 * @returns {JSX.Element}
 */
function TargetAudienceGrid({data}) {
    return (
        <div className={'target--grid'}>
            {data?.map((item, index) => (
                <div className={'target--grid-item'} key={index}>
                    <img src={item.imgSrc} alt={item.alt} className={'target--grid-item-picture'}/>
                    <h3 className={'target--grid-item-title'}>{ item.title }</h3>
                </div>
            ))}
        </div>
    );
}

/**
 * TargetAudienceGrid component
 * Renders a grid of target audience items
 * Each item includes an image and a title
 * @property {Array.<Object>} data - Array of objects containing participant data
 */
TargetAudienceGrid.propTypes = {
    data: PropTypes.arrayOf(PropTypes.object).isRequired
}

/**
 * BenefitsGrid component
 * Renders a grid of benefits panels
 * Each panel includes a title and a description
 * @param {Array.<Object>} data - Array of objects containing title and description for each benefit
 * @returns {JSX.Element}
 */
function BenefitsGrid({data}) {
    return (
        <div className={'benefits--grid'}>
            {data?.map((item, index) => (
                <div className={'benefits--grid-item'} key={index}>
                    <h3 className={'benefits--grid-item-title'}>{ item.title }</h3>
                    <p>{ item.description }</p>
                </div>
            ))}
        </div>
    );
}

/**
 * BenefitsGrid component
 * Renders a grid of benefits panels
 * Each panel includes a title and a description
 * @property {Array.<Object>} data - Array of objects containing title and description for each benefit
 */
BenefitsGrid.propTypes = {
    data: PropTypes.arrayOf(PropTypes.object).isRequired
}

/**
 * HomePage component
 * Main page of the application
 * It includes a hero section, a value proposition section, a target audience section, and a benefits section.
 * The hero section contains a title, subtitle, and a button.
 * The target audience section displays a grid of target audience items with images and titles.
 * The benefits section displays a grid of benefits panels with titles and descriptions.
 * The page is styled with CSS classes defined in home.css.
 * @returns {JSX.Element}
 */
function HomePage() {
    // Participants data
    const newParticipantsData = [
        {uid: '1', bcgImgSrc: '/pictures/png/new-participant-bcg-1.png', ppImgSrc: '/pictures/png/new-participant-pp-1.png', alt: 'Participant', title: 'Асоціація рітейлерів України', location: 'Київ, Київська обл, Закарпатська обл.'},
        {uid: '2', bcgImgSrc: '/pictures/png/new-participant-bcg-2.png', ppImgSrc: '/pictures/png/new-participant-pp-2.png', alt: 'Participant', title: 'Regno', location: 'Київ, Київська обл, Закарпатська обл.'},
        {uid: '3', bcgImgSrc: '/pictures/png/new-participant-bcg-3.png', ppImgSrc: '/pictures/png/new-participant-pp-3.png', alt: 'Participant', title: 'Мукко', location: 'Київ, Київська обл, Закарпатська обл.'},
        {uid: '4', bcgImgSrc: '/pictures/png/new-participant-bcg-4.png', ppImgSrc: '/pictures/png/new-participant-pp-4.png', alt: 'Participant', title: 'МХП', location: 'Київ, Київська обл, Закарпатська обл.'}
    ];

    // Target audience data
    const targetAudienceData = [
        {imgSrc: '/pictures/svg/bread.svg', alt: 'Bread', title: 'Виробники крафтової продукції'},
        {imgSrc: '/pictures/svg/vine.svg', alt: 'Vine', title: 'Сомельє та ресторатори'},
        {imgSrc: '/pictures/svg/building.svg', alt: 'Building', title: 'Представники готельно-ресторанного бізнесу'},
        {imgSrc: '/pictures/svg/cart.svg', alt: 'Cart', title: 'Представники роздрібних та гуртових торгових мереж'},
        {imgSrc: '/pictures/svg/box.svg', alt: 'Box', title: 'Представники пакувальної індустрії'},
        {imgSrc: '/pictures/svg/truck.svg', alt: 'Truck', title: 'Представники логістичних компаній та служб доставки'},
        {imgSrc: '/pictures/svg/rocket.svg', alt: 'Rocket', title: 'Стартапери'},
        {imgSrc: '/pictures/svg/people.svg', alt: 'People', title: 'Інші фахівці галузі'}
    ];

    // Benefits data
    const benefitsData = [
        {title: 'Прямий зв\'язок з виробниками', description: 'Знайомтеся з історією та цінностями брендів'},
        {title: 'Ексклюзивні пропозиції', description: 'Знаходьте унікальні продукти, недоступні в масовому продажі'},
        {title: 'Інновації та тренди', description: 'Будьте в курсі останніх новинок та технологій галузі'},
        {title: 'Співпраця та синергія', description: 'Об\'єднуйтесь, щоб творити нове та ділитися досвідом'},
        {title: 'Розвиток та масштабування', description: 'Знаходьте нових партнерів, клієнтів та ринки збуту'},
        {title: 'Підтримка та знання', description: 'Отримуйте консультації, експертну допомогу та доступ до освітніх ресурсів'}
    ];

    // State for changing the link text in the “New participants section”
    const [isMobile, setIsMobile] = useState(window.innerWidth <= 665);

    // Set's boolean to isMobile
    useEffect(() => {
        const handleResize = () => {
            setIsMobile(window.innerWidth <= 665);
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    return (
        <div className={'home'}>

            {/* Hero section */}
            <section className={'home--section home--section__padding-low-vertical home--section__direction-row home--section__green hero--section'}>
                <div className={'hero--title-container'}>
                    <h2 className={'hero--logo-title'}>CRAFTMERGE</h2>
                    <h2 className={'hero--text-title'}>Обʼєднуємо крафтових виробників та інноваторів</h2>
                    <div>
                        <Button className={'button__padding'}>
                            Детальніше про нас
                        </Button>
                    </div>
                </div>
                <div className={'hero--pictures'}>
                    <picture>
                        <source media="(max-width: 646px)" srcSet="/pictures/png/hero-small.png" />
                        <source media="(max-width: 1481px)" srcSet="/pictures/png/hero-middle.png" />
                        <img src={'/pictures/png/hero-big.png'} alt={'Hero'}/>
                    </picture>
                </div>
            </section>

            {/* New participants section */}
            <section className={'home--section home--section__white'}>
                <div className={'participants--title-container'}>
                    <h2 className={'home--title participants--title__flex'}>
                        Нові учасники
                    </h2>
                    <Link to={'/companies'} className={'link-right-arrow'}>
                        <p className={'participants--link link__underline'}>{isMobile ? 'Всі' : 'Всі підприємства'}</p>
                    </Link>
                </div>
                <NewParticipantGrid data={newParticipantsData} />
            </section>

            {/* Value proposition section */}
            <section className={'home--section home--section__text-align-center home--section__green'}>
                <h2 className={'home--title involve--title__max-width involve--title__margin'}>Майданчик для тих, хто втілює свої ідеї в життя</h2>
                <Button className={'involve--button__padding'}>
                    Долучитися
                </Button>
            </section>

            {/* Target audience section */}
            <section className={'home--section home--section__yellow'}>
                <h2 className={'home--title target--title__margin'}>Для кого</h2>
                <TargetAudienceGrid data={targetAudienceData} />
            </section>

            {/* Benefits section */}
            <section className={'home--section home--section__white'}>
                <h2 className={'home--title benefits--grid-item-title__margin'}>Чому варто</h2>
                <BenefitsGrid data={benefitsData} />
            </section>
        </div>
    );
}

export default HomePage;

import './whoWeAre.css';
import Image from '../../components/Image/image';

/**
 * WhoWeAre page
 * "Хто ми" (Who We Are) page that explains the platform's mission, origin, and goals,
 * So that user can understand the purpose and background of
 * CraftMerge and gain trust in the initiative.
 *
 * @component
 * @returns {JSX.Element}
 */
function WhoWeAre() {
    return (
        <div className={'wwa'}>
            <div className={'wwa--container'}>
                <h2 className={'wwa--title'}>Хто ми</h2>
                <div className={'wwa--content-container'}>
                    <div className={'wwa--content-text'}>
                        <p>
                            <span className={'wwa--content-text__bold'}>CraftMerge</span> - перший форум Західної України, який створений у співпраці з Національним університетом «Львівська політехніка». Наша місія - не лише об'єднання українських виробників та стартапів, а й відкриття нових перспектив у виробничій галузі.
                        </p>
                        <p>
                            CraftMerge - це не лише платформа для обміну досвідом та ідеями, але й комунікаційний майданчик для обговорення актуальних тенденцій та передових технологій.
                        </p>
                        <p>
                            Учасники форуму отримають можливість не лише обмінятися досвідом та ідеями, але й ознайомитися з найсучаснішими рішеннями виробництва крафтової продукції. Ми створили CraftMerge, щоб допомогти українським виробникам збільшити свою популярність та впізнаваність, розширити аудиторію споживачів та залучити нових клієнтів. Приєднуйтеся до нашого форуму та розвивайте свій бізнес разом з нами!"
                        </p>
                    </div>
                    <div className={'wwa--content-image'}>
                        <Image src={'/pictures/png/pexels-pavel-danilyuk.png'} alt={'Who we are'} className={'wwa--image'} />
                    </div>
                </div>
            </div>
        </div>
    );
}

export default WhoWeAre;

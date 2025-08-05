import './home.css';
import Button from '../../components/Button/button';

/**
 * HomePage component
 * @returns {JSX.Element}
 * @constructor
 */
function HomePage() {
    return (
        <div className={'home'}>
            <section className={'home-section home-section__green hero-section'}>
                <div className={'hero-title'}>
                    <h2 className={'home-title-1 hero-title__title-1'}>CRAFTMERGE</h2>
                    <h2 className={'home-title-2 hero-title__title-2'}>Обʼєднуємо крафтових виробників та інноваторів</h2>
                    <div>
                        <Button className={'button__padding'}>
                            Детальніше про нас
                        </Button>
                    </div>
                </div>
                <div className={'hero-pictures'}>
                    <picture>
                        <source media="(max-width: 646px)" srcSet="/pictures/png/hero-small.png" />
                        <source media="(max-width: 1481px)" srcSet="/pictures/png/hero-middle.png" />
                        <img src={'/pictures/png/hero-big.png'} alt={'Hero'}/>
                    </picture>
                </div>
            </section>

            <section className={'home-section home-section__white'}>

            </section>

            <section className={'home-section home-section__green involve-section'}>
                <h2 className={'home-title-2 involve-title'}>Майданчик для тих, хто втілює свої ідеї в життя</h2>
                <Button className={'button__padding'}>
                    Долучитися
                </Button>
            </section>

            <section className={'home-section home-section__yellow'}>

            </section>

            <section className={'home-section home-section__white'}>

            </section>
        </div>
    );
}

export default HomePage;

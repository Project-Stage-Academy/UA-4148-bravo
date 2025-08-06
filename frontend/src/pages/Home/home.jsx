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
                    <h2 className={'home-title-1 hero-title--title-1'}>CRAFTMERGE</h2>
                    <h2 className={'home-title-2 hero-title--title-2'}>Обʼєднуємо крафтових виробників та інноваторів</h2>
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
                <div className={'for-whom-section'}>
                    <h2 className={'home-title-2 for-whom-title'}>Для кого</h2>
                    <div className={'for-whom-grid'}>
                        <div className={'for-whom-grid-item'}>
                            <img src={'/pictures/svg/bread.svg'} alt={'Bread'} className={'for-whom-grid-item--picture'}/>
                            <h3 className={'for-whom-grid-item--title'}>Виробники крафтової продукції</h3>
                        </div>
                        <div className={'for-whom-grid-item'}>
                            <img src={'/pictures/svg/vine.svg'} alt={'Vine'} className={'for-whom-grid-item--picture'}/>
                            <h3 className={'for-whom-grid-item--title'}>Сомельє та ресторатори</h3>
                        </div>
                        <div className={'for-whom-grid-item'}>
                            <img src={'/pictures/svg/building.svg'} alt={'Building'} className={'for-whom-grid-item--picture'}/>
                            <h3 className={'for-whom-grid-item--title'}>Представники готельно-ресторанного бізнесу</h3>
                        </div>
                        <div className={'for-whom-grid-item'}>
                            <img src={'/pictures/svg/cart.svg'} alt={'Cart'} className={'for-whom-grid-item--picture'}/>
                            <h3 className={'for-whom-grid-item--title'}>Представники роздрібних та гуртових торгових мереж</h3>
                        </div>
                        <div className={'for-whom-grid-item'}>
                            <img src={'/pictures/svg/box.svg'} alt={'Box'} className={'for-whom-grid-item--picture'}/>
                            <h3 className={'for-whom-grid-item--title'}>Представники пакувальної індустрії</h3>
                        </div>
                        <div className={'for-whom-grid-item'}>
                            <img src={'/pictures/svg/truck.svg'} alt={'Truck'} className={'for-whom-grid-item--picture'}/>
                            <h3 className={'for-whom-grid-item--title'}>Представники логістичних компаній та служб доставки</h3>
                        </div>
                        <div className={'for-whom-grid-item'}>
                            <img src={'/pictures/svg/rocket.svg'} alt={'Rocket'} className={'for-whom-grid-item--picture'}/>
                            <h3 className={'for-whom-grid-item--title'}>Стартапери</h3>
                        </div>
                        <div className={'for-whom-grid-item'}>
                            <img src={'/pictures/svg/people.svg'} alt={'People'} className={'for-whom-grid-item--picture'}/>
                            <h3 className={'for-whom-grid-item--title'}>Інші фахівці галузі</h3>
                        </div>
                    </div>
                </div>
            </section>

            <section className={'home-section home-section__white worth-section'}>
                <h2 className={'home-title-2 worth-title'}>Чому варто</h2>
                <div className={'worth-panels-container'}>
                    <div className={'worth-panel'}>
                        <h3 className={'worth-panel--title'}>Прямий зв'язок з виробниками</h3>
                        <p>
                            Знайомтеся з історією та цінностями брендів
                        </p>
                    </div>
                    <div className={'worth-panel'}>
                        <h3 className={'worth-panel--title'}>Ексклюзивні пропозиції</h3>
                        <p>
                            Знаходьте унікальні продукти, недоступні в масовому продажі
                        </p>
                    </div>
                    <div className={'worth-panel'}>
                        <h3 className={'worth-panel--title'}>Інновації та тренди</h3>
                        <p>
                            Будьте в курсі останніх новинок та технологій галузі
                        </p>
                    </div>
                    <div className={'worth-panel'}>
                        <h3 className={'worth-panel--title'}>Співпраця та синергія</h3>
                        <p>
                            Об'єднуйтесь, щоб творити нове та ділитися досвідом
                        </p>
                    </div>
                    <div className={'worth-panel'}>
                        <h3 className={'worth-panel--title'}>Розвиток та масштабування</h3>
                        <p>
                            Знаходьте нових партнерів, клієнтів та ринки збуту
                        </p>
                    </div>
                    <div className={'worth-panel'}>
                        <h3 className={'worth-panel--title'}>Підтримка та знання</h3>
                        <p>
                            Отримуйте консультації, експертну допомогу та доступ до освітніх ресурсів
                        </p>
                    </div>
                </div>
            </section>
        </div>
    );
}

export default HomePage;

import './genericGrid.css';
import PropTypes from "prop-types";
import clsx from 'clsx';

/**
 * Grid rule set
 *
 * @component
 * @param data - data to represent
 * @param expectedLength - expectedLenght of items to display
 * @param className - additional class style
 * @param renderItem - item to render
 * @returns {JSX.Element}
 *
 * @example
 * <GenericGrid
 *     data={data}
 *     expectedLength={4}
 *     className="participants--grid"
 *     renderItem={(item) => (
 *         <ParticipantCard
 *         key={item.uid}
 *         className="participants--grid-item"
 *         uid={item.uid}
 *         bcgImgSrc={item.bcgImgSrc}
 *         ppImgSrc={item.ppImgSrc}
 *         alt={item.alt}
 *         title={item.title}
 *         location={item.location}
 *         />
 *     )}
 * />
 */
function GenericGrid({ data, expectedLength, className, renderItem }) {
    let errorMessage = null;

    if (!data) {
        errorMessage = 'Не знайдено жодних даних. Перезавантажте сторінку або спробуйте пізніше...';
    } else if (data && data.length !== expectedLength) {
        errorMessage = 'Дані пошкоджено. Перезавантажте сторінку або спробуйте пізніше...';
    }

    return !errorMessage ? (
        <div className={clsx(className)}>
            {data?.map(renderItem)}
        </div>
    ) : (
        <p>{errorMessage}</p>
    );
}

GenericGrid.propTypes = {
    data: PropTypes.arrayOf(PropTypes.object).isRequired,
    expectedLength: PropTypes.number.isRequired,
    className: PropTypes.string.isRequired,
    renderItem: PropTypes.func.isRequired
};

export default GenericGrid;

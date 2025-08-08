import "./search.css";
import PropTypes from 'prop-types';
import Button from '../Button/button';
import clsx from 'clsx';

/**
 * Search component
 */
function Search({ className }) {
    return (
        <div className={clsx('search', className)}>
            <input placeholder={"Пошук"}
                   className={"search--input"}
            />
            <Button variant="secondary" className={"search--button"}>
                <img src={"/pictures/svg/loupe.svg"} alt={"Search"}/>
            </Button>
        </div>
    );
}

/**
 * PropTypes for Search component
 * @type {{className: string}}
 */
Search.propTypes = {
    className: PropTypes.string,
};

export default Search;

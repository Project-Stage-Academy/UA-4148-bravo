import "./search.css";
import PropTypes from 'prop-types';

/**
 * Search component
 */
function Search({ className = '' }) {
    return (
        <div className={`search ${className}`}>
            <input placeholder={"Пошук"}
                   className={"search--input"}
            />
            <button className={"search--button"}>
                <img src={"/pictures/svg/loupe.svg"} alt={"Search"}/>
            </button>
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

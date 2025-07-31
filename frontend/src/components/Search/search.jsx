import "./search.css";

/**
 * Search component
 * @param {Object} props - Component properties
 * @param {string} props.width - Width of the search component
 */
function Search(props) {
    return (
        <div style={{ width: props.width }}
             className={"search"}>
            <input type="text"
                   placeholder={"Пошук"}
                   className={"input search--input"}
            />
            <button className={"search--button"}>
                <img src={"/pictures/svg/loupe.svg"} alt={"Search"}/>
            </button>
        </div>
);
}

export default Search;

import "./search.css";

function Search(props) {
    return (
        <div style={{ width: props.width }}
             className={"search"}>
            <input placeholder={"Пошук"}
                   className={"search--input"}
            />
            <button className={"search--button"}>
                <img src={"/pictures/svg/loupe.svg"} alt={"Search"}/>
            </button>
        </div>
);
}

export default Search;

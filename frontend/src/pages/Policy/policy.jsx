import './policy.css';
import data from "./policy.json";

/**
 * Policy component
 * @returns {JSX.Element}
 */
function Policy() {
    /**
     * Render text block
     * @param textBlock - text block (string or list)
     * @param index - index of the text block
     * @param paraIndex - index of the paragraph
     * @return {JSX.Element|null}
     */
    const renderText = (textBlock, index, paraIndex) => {
        if (typeof textBlock === "string") {
            return (
                <p
                    key={index}
                    aria-label={`Пункт ${paraIndex + 1}.${index + 1}`}
                >
                    {`${paraIndex + 1}.${index + 1}. ${textBlock}`.trim()}
                </p>
            );
        }

        if (textBlock.type === "list") {
            return (
                <ul
                    key={index}
                    aria-label={`Список у пункті ${paraIndex + 1}`}
                >
                    {textBlock.items.map((item, i) => (
                        <li
                            key={i}
                            aria-label={`Елемент ${paraIndex + 1}.${index + 1}.${i + 1}`.trim()}
                        >
                            {item}
                        </li>
                    ))}
                </ul>
            );
        }

        return null;
    };

    return (
        <div
            className={'policy__container'}
            aria-labelledby="policy-title"
            role="document"
        >
            <div className={'policy__text-container'}>
                {/* Main title of the document */}
                <h1
                    id="policy-title"
                    className={'policy__title policy__title--f-weight-bold'}
                >
                    {data.title}
                </h1>

                {/* Paragraphs */}
                {data.paragraphs.map((para, idx) => (
                    <section
                        key={idx}
                        className="policy__section"
                        aria-labelledby={`section-title-${idx}`}
                    >
                        <h2
                            id={`section-title-${idx}`}
                            className={'policy__title--f-weight-bold'}
                        >
                            {`${idx + 1}. ${para.title}`}
                        </h2>
                        {para.text.map((block, i) => renderText(block, i, idx))}
                    </section>
                ))}
            </div>
        </div>
    );
}

export default Policy;

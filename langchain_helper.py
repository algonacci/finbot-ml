from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_openai import ChatOpenAI


def classify_template(message):
    classification_template = PromptTemplate.from_template(
        """
        You are a highly accurate classifier for finance-related questions. 
        You must classify the user’s question into exactly one of the following categories:

        1. **Finance Metrics** 
        - Questions about specific financial metrics or stock performance.
        - Examples: PE ratio, EPS, market cap, price, share volume, dividend, daily price changes, etc.
        - Any question about “How is the stock performing?”, “What is the current price/price movement today?”, 
            “Is the stock going up or down today?”, or *any numeric aspect* related to the company's stock performance.

        2. **Latest News**
        - Questions about recent news or updates related to the stock or the company. 
        - Examples: new product launches, official press releases, management changes, or major announcements.

        3. **General Info**
        - Questions about general company information that do *not* center on financial metrics or the latest news.
        - Examples: founding history, founder’s name, business model, company structure, or location.

        Below are some illustrative examples:

        - Example 1:
        Q: "Berapa harga saham [XYZ] hari ini?"
        A: Finance Metrics

        - Example 2:
        Q: "PE ratio [XYZ] itu berapa?"
        A: Finance Metrics

        - Example 3:
        Q: "Ada kabar apa terbaru soal [XYZ] minggu ini?"
        A: Latest News

        - Example 4:
        Q: "Kapan perusahaan [XYZ] berdiri dan siapa pendirinya?"
        A: General Info

        - Example 5:
        Q: "Bagaimana perkembangan harga saham [XYZ] sepanjang tahun ini?"
        A: Finance Metrics

        - Example 6:
        Q: "Siapa CEO [XYZ] sekarang?"
        A: General Info

        <question>
        {question}
        </question>

        Please output the classification only, without explanation. 
        Classification:
        """
    )

    classification_chain = (
        classification_template
        | ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        | StrOutputParser()
    )

    classification_result = classification_chain.invoke({"question": message})

    print(classification_result)

    return classification_result


def format_search_results(results):
    formatted = []
    for result in results:
        formatted.append(
            f"Source: {result.get('url', 'N/A')}\nContent: {result.get('raw_content', '')}\n"
        )
    return "\n".join(formatted)

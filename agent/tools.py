from langchain_community.tools import DuckDuckGoSearchRun

search = DuckDuckGoSearchRun(
    description=(
        "Search the internet for up-to-date financial information including stock prices, "
        "market data, company earnings, economic indicators, and financial news."
    )
)

tools = [search]

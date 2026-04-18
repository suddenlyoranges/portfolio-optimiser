from matplotlib import ticker, pyplot as plt
from yahoofinancials import YahooFinancials
from abc import ABC, abstractmethod
import pandas as pd
import enum

user_ticker=input("Enter stock ticker (default: AAPL): ") or "AAPL"
class Frequency(enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class StockPriceDatasetAdapter(ABC):
    """
    Interface to access any data source of stock price quotes.
    """
    

    DEFAULT_TICKER = user_ticker

    @property
    @abstractmethod
    def training_set(self):
        """Return training dataset (DataFrame with time & stock price)."""
        pass

    @property
    @abstractmethod
    def validation_set(self):
        """Return validation dataset (DataFrame with time & stock price)."""
        pass


class BaseStockPriceDatasetAdapter(StockPriceDatasetAdapter):
    def __init__(self, ticker: str = None):
        self._ticker = ticker or self.DEFAULT_TICKER
        self._training_set = None
        self._validation_set = None

    @abstractmethod
    def _connect_and_prepare(self, date_range: tuple):
        """
        Connect to data source and return records within date range.
        """
        pass

    @property
    def training_set(self):
        return self._training_set.copy()

    @property
    def validation_set(self):
        return self._validation_set.copy()


class YahooFinancialsAdapter(BaseStockPriceDatasetAdapter):
    """
    Dataset adapter for Yahoo Financials.
    """

    def __init__(
        self,
        ticker=StockPriceDatasetAdapter.DEFAULT_TICKER,
        frequency=Frequency.DAILY,
        training_set_date_range=("2020-01-01", "2021-12-31"),
        validation_set_date_range=("2013-07-01", "2013-08-31"),
    ):
        super().__init__(ticker=ticker)

        self._frequency = frequency
        self._yf = YahooFinancials(self._ticker)

        # Load datasets
        self._training_set = self._connect_and_prepare(training_set_date_range)
        self._validation_set = self._connect_and_prepare(validation_set_date_range)

    def _connect_and_prepare(self, date_range: tuple):
        records = self._yf.get_historical_price_data(
            date_range[0],
            date_range[1],
            self._frequency.value
        )[self._ticker]

        if "prices" not in records or not records["prices"]:
          raise ValueError(f"No price data available for ticker: {self._ticker}")

        df = pd.DataFrame(records["prices"])[["formatted_date", "close"]]

        # Rename columns
        df.rename(
            columns={"formatted_date": "time", "close": "stock price"},
            inplace=True
        )

        df["time"] = pd.to_datetime(df["time"])

        return df
    
def plot_actual(df, ticker_name):
    plt.figure()

    plt.plot(df["time"], df["stock price"])

    plt.title(f"{ticker_name} Stock Price")
    plt.xlabel("Time")
    plt.ylabel("Stock Price")

    # Rotate dates for readability
    plt.xticks(rotation=45)

    # Optional: cleaner axis formatting
    plt.gca().xaxis.set_major_locator(plt.MaxNLocator(10))

    plt.tight_layout()
    plt.show()

def compute_returns():
    monthly = YahooFinancialsAdapter(ticker=user_ticker, frequency=Frequency.MONTHLY).training_set
    #   R_t = S_t/S_(t-1) - 1
    monthly['Return'] = monthly['stock price']/monthly['stock price'].shift(1) - 1
    weekly = YahooFinancialsAdapter(ticker=user_ticker, frequency=Frequency.WEEKLY).training_set
    weekly['Return'] = weekly['stock price']/weekly['stock price'].shift(1) - 1
    daily = YahooFinancialsAdapter(ticker=user_ticker, frequency=Frequency.DAILY).training_set
    daily['Return'] = daily['stock price']/daily['stock price'].shift(1) - 1
    periodic_returns = [('Daily', daily), ('Weekly', weekly), ('Monthly', monthly)]
    return periodic_returns
    
def plot_returns(df, label):
    plt.figure()

    plt.plot(df["time"], df["Return"])

    plt.title(f"{label} Returns")
    plt.xlabel("Time")
    plt.ylabel("Return")

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    
def plot_all_returns(periodic_returns):
    plt.figure()

    for label, df in periodic_returns:
        df["time"] = pd.to_datetime(df["time"])
        plt.plot(df["time"], df["Return"], label=label)

    plt.title("Stock Returns Comparison")
    plt.xlabel("Time")
    plt.ylabel("Return")

    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    adapter = YahooFinancialsAdapter(ticker=user_ticker)

    print (f"Ticker: {adapter._ticker}")

    print("Training set:")
    print(adapter.training_set.head())

    print("\nValidation set:")
    print(adapter.validation_set.head())

    #plot_actual(adapter.training_set, adapter._ticker)

    returns_data = compute_returns()
    plot_all_returns(returns_data)
"""
Stock Data Collector

This module is responsible for collecting stock price data from the Finnhub API.
"""
import requests
import logging

class StockCollector:
    def __init__(self, api_key, stocks_to_collect=None):
        """
        Initialize the stock collector.
        
        Args:
            api_key: Finnhub API key
            stocks_to_collect: List of stock symbols to collect data for.
                               If None, will attempt to get from server.
        """
        self.api_key = api_key
        self.stocks_to_collect = stocks_to_collect or []
        
    def get_stocks_from_server(self, server_url):
        """
        Get list of stock symbols to monitor from the server.
        
        Args:
            server_url: The URL of the monitoring server
            
        Returns:
            List of stock symbols or empty list if failed
        """
        try:
            response = requests.get(f"{server_url}/metrics/stock/symbols")
            if response.status_code == 200:
                return response.json()
            else:
                logging.warning(f"Failed to get stock symbols: {response.status_code}")
                return []
        except Exception as e:
            logging.error(f"Error getting stock symbols: {e}")
            return []
    
    def update_stocks_list(self, server_url):
        """
        Update the internal list of stocks to collect with data from server
        if no stocks were provided during initialization.
        
        Args:
            server_url: The URL of the monitoring server
        """
        if not self.stocks_to_collect:
            self.stocks_to_collect = self.get_stocks_from_server(server_url)
            logging.info(f"Updated stocks list from server: {self.stocks_to_collect}")
    
    def add_stock(self, symbol):
        """
        Add a stock to the collection list if not already there.
        
        Args:
            symbol: Stock symbol to add
        """
        symbol = symbol.upper()
        if symbol not in self.stocks_to_collect:
            self.stocks_to_collect.append(symbol)
            logging.info(f"Added {symbol} to stock collection list")
    
    def collect_stock_data(self):
        """
        Collect current price data for all configured stocks.
        
        Returns:
            Dict mapping stock symbols to their current prices
        """
        results = {}
        
        for symbol in self.stocks_to_collect:
            price = self.get_stock_price(symbol)
            if price is not None:
                results[symbol] = price
        
        return results
    
    def get_stock_price(self, symbol):
        """
        Get the current price for a specific stock symbol.
        
        Args:
            symbol: Stock symbol to get price for
            
        Returns:
            Current price or None if request failed
        """
        try:
            finnhub_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={self.api_key}"
            response = requests.get(finnhub_url)
            
            if response.status_code == 200:
                stock_data = response.json()
                price = stock_data['c']  # Current price
                logging.info(f"Got price for {symbol}: ${price}")
                return price
            else:
                logging.warning(f"Failed to get stock data for {symbol}: {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"Error fetching stock data for {symbol}: {e}")
            return None 
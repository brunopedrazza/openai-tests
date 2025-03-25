from coinbase.rest import RESTClient
import uuid
from typing import Optional, Dict, Any, Tuple
import os

class CoinbaseService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CoinbaseService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize Coinbase client with credentials from environment variables"""
        self.api_key = os.environ.get("COINBASE_API_KEY")
        self.api_secret = os.environ.get("COINBASE_API_SECRET")
        
        if not all([self.api_key, self.api_secret]):
            raise ValueError("Coinbase credentials not configured. Please set COINBASE_API_KEY and COINBASE_API_SECRET environment variables.")
        
        self.client = RESTClient(
            api_key=self.api_key,
            api_secret=self.api_secret
        )

    def get_balance(self, asset: str) -> Optional[float]:
        """Get the balance of a specific asset"""
        try:
            balance_response = self.client.get_accounts()
            for account in balance_response.accounts:
                if account.currency == asset:
                    return float(account.available_balance["value"])
            return 0.0
        except Exception as e:
            return None

    def get_usdc_balance(self) -> Optional[float]:
        """Get USDC balance"""
        return self.get_balance("USDC")

    def get_product_details(self, asset: str) -> Tuple[float, int, int]:
        """
        Get product details including current price and decimal places
        Returns: (current_price, base_decimal_places, quote_decimal_places)
        """
        product_id = f"{asset}-USDC"
        product = self.client.get_product(product_id=product_id)
        current_price = float(product.price)
        base_decimal_places = len(product.base_increment.split('.')[-1])
        quote_decimal_places = len(product.quote_increment.split('.')[-1])
        return current_price, base_decimal_places, quote_decimal_places

    def create_market_buy_order(self, product_id: str, quote_size: str) -> Dict[str, Any]:
        """Create a market buy order"""
        client_order_id = str(uuid.uuid4())
        order = self.client.market_order_buy(
            client_order_id=client_order_id,
            product_id=product_id,
            quote_size=quote_size
        )
        return self._process_order_response(order)

    def create_market_sell_order(self, product_id: str, base_size: str) -> Dict[str, Any]:
        """Create a market sell order"""
        client_order_id = str(uuid.uuid4())
        order = self.client.market_order_sell(
            client_order_id=client_order_id,
            product_id=product_id,
            base_size=base_size
        )
        return self._process_order_response(order)

    def _process_order_response(self, order) -> Dict[str, Any]:
        """Process the order response"""
        if not order.success:
            return {
                "success": False,
                "error": order.error_response
            }
        
        return {
            "success": True,
            "order_id": order.success_response["order_id"],
            "product_id": order.success_response["product_id"],
            "side": order.success_response["side"]
        } 
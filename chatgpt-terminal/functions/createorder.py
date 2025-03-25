from functions.functioncallingbase import FunctionCallingBase
from services.coinbase_service import CoinbaseService

class CreateOrder(FunctionCallingBase):
    def __init__(self):
        super().__init__()
        self.coinbase_service = CoinbaseService()

    def _get_function_definition(self):
        return {
            "name": "create_order",
            "description": "Create a market order to buy or sell a crypto asset on an exchange.",
            "operation_type": "write",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["buy", "sell"]},
                    "amountInDollars": {
                        "type": ["number", "string"],
                        "description": "The amount in dollars for the trade, or 'all' to use entire balance"
                    },
                    "asset": {"type": "string", "description": "The asset to take the action in, must be the symbol of the asset in upper case"}
                },
                "required": ["action", "amountInDollars", "asset"],
                "additionalProperties": False
            }
        }

    def execute(self, **kwargs):
        action = kwargs.get("action")
        amountInDollars = kwargs.get("amountInDollars")
        asset = kwargs.get("asset")

        try:
            # Format the product ID (e.g., "BTC" becomes "BTC-USDC")
            product_id = f"{asset}-USDC"
            
            # Get product details to determine decimal precision
            current_price, base_decimal_places, quote_decimal_places = self.coinbase_service.get_product_details(asset)

            # Handle "all" amounts
            if amountInDollars == "all":
                if action.lower() == "buy":
                    # Get available USDC balance
                    usdc_balance = self.coinbase_service.get_usdc_balance()
                    if usdc_balance is None:
                        return {"success": False, "error": "Failed to fetch USDC balance"}
                    amountInDollars = usdc_balance
                else:  # sell
                    # Get available asset balance
                    asset_balance = self.coinbase_service.get_balance(asset)
                    if asset_balance is None:
                        return {"success": False, "error": f"Failed to fetch {asset} balance"}
                    if action.lower() == "sell":
                        # For sell orders, we already have the base size (asset amount)
                        base_size = str(round(asset_balance, base_decimal_places))
                        result = self.coinbase_service.create_market_sell_order(product_id, base_size)
                        if result["success"]:
                            result["price"] = current_price
                            result["rounded_amount"] = base_size
                        return result
                    amountInDollars = asset_balance * current_price
            
            if action.lower() == "buy":
                # Round the quote size (USDC amount) to appropriate precision
                quote_size = str(round(amountInDollars, quote_decimal_places))
                result = self.coinbase_service.create_market_buy_order(product_id, quote_size)
                if result["success"]:
                    result["price"] = current_price
                    result["rounded_amount"] = quote_size
                return result
            else:  # sell
                # Calculate base size and round to appropriate precision
                raw_base_size = amountInDollars / current_price
                # Round to the number of decimals specified by base_increment
                base_size = str(round(raw_base_size, base_decimal_places))
                result = self.coinbase_service.create_market_sell_order(product_id, base_size)
                if result["success"]:
                    result["price"] = current_price
                    result["rounded_amount"] = base_size
                return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
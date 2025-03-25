from functions.functioncallingbase import FunctionCallingBase
from services.coinbase_service import CoinbaseService

class GetBalance(FunctionCallingBase):
    def __init__(self):
        super().__init__()
        self.coinbase_service = CoinbaseService()

    def _get_function_definition(self):
        return {
            "name": "get_balance",
            "description": "Get the balance of a specific crypto asset in your account",
            "operation_type": "read",
            "parameters": {
                "type": "object",
                "properties": {
                    "asset": {
                        "type": "string",
                        "description": "The asset symbol in upper case, or 'USDC' for USDC balance"
                    }
                },
                "required": ["asset"],
                "additionalProperties": False
            }
        }

    def execute(self, **kwargs):
        asset = kwargs.get("asset")
        try:
            balance = self.coinbase_service.get_balance(asset)

            if balance is None:
                return {
                    "success": False,
                    "error": f"Failed to fetch {asset} balance"
                }

            return {
                "success": True,
                "asset": asset,
                "balance": balance
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
import json
import uuid
from openai import OpenAI
from coinbase.rest import RESTClient
import os
tools = [{
    "type": "function",
    "function": {
        "name": "create_order",
        "description": "Create a market order to buy or sell a crypto asset on an exchange. Use 'all' as amountInDollars to either sell entire balance of asset or buy using all available USDC. If no amount is specified or is not clear, use all",
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
        },
        "strict": True
    }
}]

def get_balance(client: RESTClient, asset):
    try:
        balance_response = client.get_accounts()
        for account in balance_response.accounts:
            if account.currency == asset:
                return float(account.available_balance["value"])
        return 0.0
    except Exception as e:
        return None

def get_usdc_balance(client):
    return get_balance(client, "USDC")

def create_order(action, amountInDollars, asset):
    try:
        # Initialize Coinbase client (uses API key and secret from environment variables)
        coinbase_client = RESTClient(
            api_key=os.getenv("COINBASE_API_KEY"),
            api_secret=os.getenv("COINBASE_API_SECRET")
        )
        
        # Format the product ID (e.g., "BTC" becomes "BTC-USDC")
        product_id = f"{asset}-USDC"
        
        # Get product details to determine decimal precision
        product = coinbase_client.get_product(product_id=product_id)
        current_price = float(product.price)
        base_decimal_places = len(product.base_increment.split('.')[-1])
        quote_decimal_places = len(product.quote_increment.split('.')[-1])
        
        # Generate a unique client order ID
        client_order_id = str(uuid.uuid4())

        # Handle "all" amounts
        if amountInDollars == "all":
            if action.lower() == "buy":
                # Get available USDC balance
                usdc_balance = get_usdc_balance(coinbase_client)
                if usdc_balance is None:
                    return {"success": False, "error": "Failed to fetch USDC balance"}
                amountInDollars = usdc_balance
            else:  # sell
                # Get available asset balance
                asset_balance = get_balance(coinbase_client, asset)
                if asset_balance is None:
                    return {"success": False, "error": f"Failed to fetch {asset} balance"}
                if action.lower() == "sell":
                    # For sell orders, we already have the base size (asset amount)
                    base_size = str(round(asset_balance, base_decimal_places))
                    order = coinbase_client.market_order_sell(
                        client_order_id=client_order_id,
                        product_id=product_id,
                        base_size=base_size
                    )
                    if not order.success:
                        return {
                            "success": False,
                            "error": order.error_response
                        }
                    return {
                        "success": True,
                        "order_id": order.success_response["order_id"],
                        "product_id": order.success_response["product_id"],
                        "side": order.success_response["side"],
                        "price": current_price,
                        "rounded_amount": base_size
                    }
                amountInDollars = asset_balance * current_price
        
        if action.lower() == "buy":
            # Round the quote size (USDC amount) to appropriate precision
            quote_size = str(round(amountInDollars, quote_decimal_places))
            
            order = coinbase_client.market_order_buy(
                client_order_id=client_order_id,
                product_id=product_id,
                quote_size=quote_size
            )
        else:  # sell
            # Calculate base size and round to appropriate precision
            raw_base_size = amountInDollars / current_price
            # Round to the number of decimals specified by base_increment
            base_size = str(round(raw_base_size, base_decimal_places))
            
            order = coinbase_client.market_order_sell(
                client_order_id=client_order_id,
                product_id=product_id,
                base_size=base_size
            )
        
        if not order.success:
            return {
                "success": False,
                "error": order.error_response
            }
        
        return {
            "success": True,
            "order_id": order.success_response["order_id"],
            "product_id": order.success_response["product_id"],
            "side": order.success_response["side"],
            "price": current_price,
            "rounded_amount": quote_size if action.lower() == "buy" else base_size
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    client = OpenAI()

    user_input = input("Enter your crypto trading action: ")

    messages = [{
        "role": "user", 
        "content": user_input
    }]

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
    )

    tool_call = completion.choices[0].message.tool_calls[0]
    args = json.loads(tool_call.function.arguments)

    result = create_order(args["action"], args["amountInDollars"], args["asset"])

    messages.append(completion.choices[0].message)
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": str(result)
    })

    completion_2 = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
    )

    print(completion_2.choices[0].message.content)

if __name__ == '__main__':
    main() 
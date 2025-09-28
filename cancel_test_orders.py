from myfalconadvisor.tools.alpaca_trading_service import alpaca_trading_service
from alpaca.trading.requests import GetOrdersRequest

def cancel_test_orders():
    try:
        # Get all open orders
        orders = alpaca_trading_service.trading_client.get_orders(GetOrdersRequest(status='open'))
        
        # Find test SPY orders (1 share orders)
        test_orders = [order for order in orders 
                      if order.symbol == "SPY" and float(order.qty) == 1.0]
        
        if not test_orders:
            print("No test orders found")
            return
            
        print(f"Found {len(test_orders)} test orders to cancel:")
        for order in test_orders:
            try:
                alpaca_trading_service.trading_client.cancel_order_by_id(order.id)
                print(f"Cancelled order {order.id} (SPY x1)")
            except Exception as e:
                print(f"Failed to cancel order {order.id}: {e}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    cancel_test_orders()

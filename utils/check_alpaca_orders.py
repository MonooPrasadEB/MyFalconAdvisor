from myfalconadvisor.tools.alpaca_trading_service import alpaca_trading_service
from alpaca.trading.requests import GetOrdersRequest

def check_pending_orders():
    try:
        orders = alpaca_trading_service.trading_client.get_orders(GetOrdersRequest(status='open'))
        
        print('\n=== PENDING ALPACA ORDERS ===')
        if not orders:
            print('No pending orders found')
            return
            
        print(f'Found {len(orders)} pending orders:')
        total_value = 0
        
        for order in orders:
            print(f'\nSymbol: {order.symbol}')
            print(f'Side: {order.side}')
            print(f'Quantity: {order.qty}')
            print(f'Type: {order.type}')
            print(f'Status: {order.status}')
            print(f'Submitted: {order.submitted_at}')
            
            # For market orders, get current price
            if order.type == 'market':
                try:
                    quote = alpaca_trading_service.data_client.get_stock_latest_quote(order.symbol)
                    est_price = (quote.ask_price + quote.bid_price) / 2
                    print(f'Estimated Market Price: ${est_price:.2f}')
                    total_value += float(order.qty) * est_price
                except:
                    print('Could not estimate market price')
            # For limit orders
            elif hasattr(order, 'limit_price') and order.limit_price:
                print(f'Limit Price: ${order.limit_price}')
                total_value += float(order.qty) * float(order.limit_price)
                
        if total_value > 0:
            print(f'\nTotal Estimated Value: ${total_value:,.2f}')
        
    except Exception as e:
        print(f'Error checking orders: {e}')

if __name__ == '__main__':
    check_pending_orders()
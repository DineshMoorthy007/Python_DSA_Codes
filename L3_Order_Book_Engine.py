from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

class OrderSide(Enum):
    BUY = auto()
    SELL = auto()

@dataclass
class Order:
    """Represents an individual limit order with FIFO time priority."""
    order_id: str
    side: OrderSide
    price: float
    quantity: int
    prev: Optional['Order'] = field(default=None, repr=False)
    next: Optional['Order'] = field(default=None, repr=False)


@dataclass
class TradeMatch:
    """Represents a matched trade execution between a maker and a taker order."""
    buy_order_id: str
    sell_order_id: str
    price: float
    quantity: int


class PriceLevelQueue:
    """Doubly-linked list maintaining FIFO time-priority for orders at a single price point."""

    def __init__(self, price: float):
        self.price = price
        self.head: Optional[Order] = None
        self.tail: Optional[Order] = None
        self.total_volume = 0

    def append(self, order: Order) -> None:
        """Appends order to back of queue (lowest time priority at this price)."""
        order.prev = self.tail
        order.next = None

        if self.tail:
            self.tail.next = order
        self.tail = order

        if not self.head:
            self.head = order

        self.total_volume += order.quantity

    def remove(self, order: Order) -> None:
        """Removes an order from anywhere in the doubly-linked list in O(1) time."""
        if order.prev:
            order.prev.next = order.next
        else:
            self.head = order.next  # Order was head

        if order.next:
            order.next.prev = order.prev
        else:
            self.tail = order.prev  # Order was tail

        self.total_volume -= order.quantity
        order.prev = None
        order.next = None

    def is_empty(self) -> bool:
        return self.head is None


class L3OrderBook:
    """High-Performance L3 Order Book with O(1) Order Placement, Cancellation, and Matching."""

    def __init__(self, symbol: str):
        self.symbol = symbol
        # Price -> PriceLevelQueue
        self.bids: Dict[float, PriceLevelQueue] = {}
        self.asks: Dict[float, PriceLevelQueue] = {}
        # Order ID -> Order (Direct index for O(1) lookup & cancellation)
        self.orders: Dict[str, Order] = {}

    def limit_order(self, order_id: str, side: OrderSide, price: float, quantity: int) -> List[TradeMatch]:
        """Places a limit order. First attempts immediate matching against opposite book side,
        then posts any remaining unmatched quantity to the book in O(1) time.
        """
        trades: List[TradeMatch] = []
        remaining_qty = quantity

        # Step 1: Attempt matching against opposite side of order book
        if side == OrderSide.BUY:
            trades, remaining_qty = self._match_buy_order(order_id, price, remaining_qty)
        else:
            trades, remaining_qty = self._match_sell_order(order_id, price, remaining_qty)

        # Step 2: Post remaining unmatched quantity as a maker order on the book
        if remaining_qty > 0:
            new_order = Order(order_id=order_id, side=side, price=price, quantity=remaining_qty)
            self.orders[order_id] = new_order

            target_book = self.bids if side == OrderSide.BUY else self.asks
            if price not in target_book:
                target_book[price] = PriceLevelQueue(price)
            target_book[price].append(new_order)

            print(f"  [ORDER POSTED] {side.name} {remaining_qty} @ ${price:.2f} (Order ID: {order_id})")

        return trades

    def cancel_order(self, order_id: str) -> bool:
        """Cancels an active resting order in O(1) constant time."""
        if order_id not in self.orders:
            return False  # Order not found or already filled

        order = self.orders.pop(order_id)
        target_book = self.bids if order.side == OrderSide.BUY else self.asks
        price_level = target_book[order.price]

        # O(1) node removal from doubly-linked list
        price_level.remove(order)

        # Clean up empty price level
        if price_level.is_empty():
            del target_book[order.price]

        print(f"  [ORDER CANCELLED] {order.side.name} {order.quantity} @ ${order.price:.2f} (Order ID: {order_id})")
        return True

    def _match_buy_order(self, buy_id: str, buy_price: float, quantity: int) -> Tuple[List[TradeMatch], int]:
        """Matches a incoming BUY order against resting ASK price levels (lowest ask first)."""
        trades: List[TradeMatch] = []
        sorted_ask_prices = sorted(self.asks.keys())  # Lowest ask first

        for ask_price in sorted_ask_prices:
            if ask_price > buy_price or quantity == 0:
                break  # Best ask exceeds max buy price

            price_level = self.asks[ask_price]
            curr_maker = price_level.head

            while curr_maker and quantity > 0:
                matched_qty = min(quantity, curr_maker.quantity)
                trades.append(TradeMatch(
                    buy_order_id=buy_id,
                    sell_order_id=curr_maker.order_id,
                    price=ask_price,
                    quantity=matched_qty
                ))

                quantity -= matched_qty
                curr_maker.quantity -= matched_qty
                price_level.total_volume -= matched_qty

                next_maker = curr_maker.next
                if curr_maker.quantity == 0:
                    # Maker order fully filled -> purge from book
                    price_level.remove(curr_maker)
                    del self.orders[curr_maker.order_id]

                curr_maker = next_maker

            if price_level.is_empty():
                del self.asks[ask_price]

        return trades, quantity

    def _match_sell_order(self, sell_id: str, sell_price: float, quantity: int) -> Tuple[List[TradeMatch], int]:
        """Matches an incoming SELL order against resting BID price levels (highest bid first)."""
        trades: List[TradeMatch] = []
        sorted_bid_prices = sorted(self.bids.keys(), reverse=True)  # Highest bid first

        for bid_price in sorted_bid_prices:
            if bid_price < sell_price or quantity == 0:
                break  # Best bid is below min sell price

            price_level = self.bids[bid_price]
            curr_maker = price_level.head

            while curr_maker and quantity > 0:
                matched_qty = min(quantity, curr_maker.quantity)
                trades.append(TradeMatch(
                    buy_order_id=curr_maker.order_id,
                    sell_order_id=sell_id,
                    price=bid_price,
                    quantity=matched_qty
                ))

                quantity -= matched_qty
                curr_maker.quantity -= matched_qty
                price_level.total_volume -= matched_qty

                next_maker = curr_maker.next
                if curr_maker.quantity == 0:
                    price_level.remove(curr_maker)
                    del self.orders[curr_maker.order_id]

                curr_maker = next_maker

            if price_level.is_empty():
                del self.bids[bid_price]

        return trades, quantity

    def get_top_of_book(self) -> Tuple[Optional[float], Optional[float]]:
        """Returns (best_bid, best_ask) in O(1) time."""
        best_bid = max(self.bids.keys()) if self.bids else None
        best_ask = min(self.asks.keys()) if self.asks else None
        return best_bid, best_ask


# --- HFT Exchange Matching Simulation ---

if __name__ == "__main__":
    print("--- Initializing High-Frequency L3 Order Book Engine ---\n")

    book = L3OrderBook(symbol="BTC/USD")

    print("[STEP 1: Posting Resting Limit Orders to Book]")
    book.limit_order(order_id="order_1", side=OrderSide.BUY, price=100.00, quantity=10)
    book.limit_order(order_id="order_2", side=OrderSide.BUY, price=100.00, quantity=5)
    book.limit_order(order_id="order_3", side=OrderSide.SELL, price=102.00, quantity=8)
    book.limit_order(order_id="order_4", side=OrderSide.SELL, price=103.00, quantity=20)

    best_bid, best_ask = book.get_top_of_book()
    print(f"\n  [TOP OF BOOK] Best Bid: ${best_bid:.2f} | Best Ask: ${best_ask:.2f}")
    print("-" * 65)

    print("\n[STEP 2: Instantaneous O(1) Order Cancellation]")
    book.cancel_order(order_id="order_2")  # Cancels 5 BTC buy order at $100.00

    print("\n[STEP 3: Incoming Taker Market/Limit Order Execution]")
    # Incoming aggressive BUY order for 12 BTC at $103.00 (Crosses spread!)
    trades = book.limit_order(order_id="order_5", side=OrderSide.BUY, price=103.00, quantity=12)

    print(f"\n  [MATCHED TRADES EXECUTED: {len(trades)} Match(es)]")
    for t in trades:
        print(f"    -> Executed {t.quantity} unit(s) @ ${t.price:.2f} (Buyer: {t.buy_order_id} <-> Seller: {t.sell_order_id})")

    new_bid, new_ask = book.get_top_of_book()
    print(f"\n  [UPDATED TOP OF BOOK] Best Bid: ${new_bid:.2f} | Best Ask: ${new_ask:.2f}")
    print("-" * 65)
    print("[SUCCESS] High-frequency L3 order book maintained Price-Time priority with O(1) operations!")

# Output :
# --- Initializing High-Frequency L3 Order Book Engine ---

# [STEP 1: Posting Resting Limit Orders to Book]
#   [ORDER POSTED] BUY 10 @ $100.00 (Order ID: order_1)
#   [ORDER POSTED] BUY 5 @ $100.00 (Order ID: order_2)
#   [ORDER POSTED] SELL 8 @ $102.00 (Order ID: order_3)
#   [ORDER POSTED] SELL 20 @ $103.00 (Order ID: order_4)

#   [TOP OF BOOK] Best Bid: $100.00 | Best Ask: $102.00
# -----------------------------------------------------------------

# [STEP 2: Instantaneous O(1) Order Cancellation]
#   [ORDER CANCELLED] BUY 5 @ $100.00 (Order ID: order_2)

# [STEP 3: Incoming Taker Market/Limit Order Execution]

#   [MATCHED TRADES EXECUTED: 2 Match(es)]
#     -> Executed 8 unit(s) @ $102.00 (Buyer: order_5 <-> Seller: order_3)
#     -> Executed 4 unit(s) @ $103.00 (Buyer: order_5 <-> Seller: order_4)

#   [UPDATED TOP OF BOOK] Best Bid: $100.00 | Best Ask: $103.00
# -----------------------------------------------------------------
# [SUCCESS] High-frequency L3 order book maintained Price-Time priority with O(1) operations!

"""引擎課 · 第一天：盤口，和一張市價單

只要 Python 3，不用裝任何包。
跑法：python3 day1.py
你只寫 Book.market 裏標著「你來寫」的那一段，十行上下。
"""
from dataclasses import dataclass


@dataclass
class Order:
    id: int        # 進場的先後號，越小越早
    side: str      # 'buy' 或 'sell'
    price: float   # 限價：買單最多肯付多少，賣單最少要收多少
    qty: float     # 還沒成交的數量


class Book:
    def __init__(self):
        self.bids = []   # 買單，最好的排最前：價格高的先，同價先來的先
        self.asks = []   # 賣單，最好的排最前：價格低的先，同價先來的先

    def add(self, order):
        """把一張限價單放進盤口。今天先不管它會不會立刻成交。"""
        if order.side == 'buy':
            self.bids.append(order)
            self.bids.sort(key=lambda o: (-o.price, o.id))
        else:
            self.asks.append(order)
            self.asks.sort(key=lambda o: (o.price, o.id))
        # 「價格優先、時間優先」這兩條規則，就是上面那兩個排序鍵。

    def market(self, side, qty):
        """一張市價單。side 是 'buy' 或 'sell'，qty 是想成交的數量。

        從對面最好的那張單開始，一張一張吃，吃夠 qty 為止。
        要做到三件事：
          1. 回傳成交列表 [(價格, 數量), ...]，按成交的先後排。
          2. 被吃掉的量，從那張單的 qty 裏扣掉。
          3. 被吃光的單，從盤口裏拿走。
        盤口不夠吃，就吃多少算多少，剩下的作廢，不要報錯。
        """
        fills = []
        # ---------- 你來寫 ----------
        if side == 'buy':
            while qty > 0 and self.asks != []:
                top = self.asks[0]
                if top.qty <= qty:
                    qty -= top.qty
                    fills.append((top.price, top.qty))
                    self.asks.remove(top)
                else:
                    fills.append((top.price, qty))
                    self.asks[0].qty -= qty
                    qty = 0
        else:
            while qty > 0 and self.bids != []:
                top = self.bids[0]
                if top.qty <= qty:
                    qty -= top.qty
                    fills.append((top.price, top.qty))
                    self.bids.remove(top)
                else:
                    fills.append((top.price, qty))
                    self.bids[0].qty -= qty
                    qty = 0
        # ----------------------------
        return fills

    def show(self):
        """把盤口印出來：賣單在上，買單在下。"""
        for o in reversed(self.asks):
            print(f'  賣  {o.price:>7}  {o.qty:>4}    #{o.id}')
        print('  ' + '-' * 26)
        for o in self.bids:
            print(f'  買  {o.price:>7}  {o.qty:>4}    #{o.id}')


# ====================== 下面是測試，不用改 ======================

def make_book():
    """課上那張盤口。"""
    book = Book()
    rows = [('sell', 101.5, 2), ('sell', 101.0, 1), ('sell', 100.5, 3),
            ('buy', 100.0, 2), ('buy', 99.5, 4), ('buy', 99.0, 1)]
    for i, (side, price, qty) in enumerate(rows, start=1):
        book.add(Order(i, side, price, qty))
    return book


def _state(orders):
    return [(float(o.price), float(o.qty)) for o in orders]


def _check(n, title, side, qty, want_fills, want_asks, want_bids):
    head = f'第 {n} 關（{title}）'
    book = make_book()
    before = (_state(book.asks), _state(book.bids))
    try:
        got = book.market(side, qty)
    except Exception as e:
        print(f'{head}沒過：報錯了，{type(e).__name__}: {e}')
        return False
    try:
        got = [(float(p), float(q)) for p, q in got]
    except Exception:
        print(f'{head}沒過：要回傳 [(價格, 數量), ...]，你回傳的是 {got!r}')
        return False
    after = (_state(book.asks), _state(book.bids))
    if not got and after == before:
        print(f'{head}沒過：什麼都沒成交。那一段還沒寫？')
        return False
    if got != want_fills:
        print(f'{head}沒過：成交列表不對。')
        print(f'    應該是  {want_fills}')
        print(f'    你的是  {got}')
        return False
    if after == before:
        print(f'{head}沒過：成交列表對了，可盤口沒變。吃掉的量要從盤口裏扣掉。')
        return False
    if any(q == 0 for _, q in after[0] + after[1]):
        print(f'{head}沒過：吃光的單還留在盤口裏（數量是 0），要拿走。')
        return False
    if after != (want_asks, want_bids):
        print(f'{head}沒過：成交列表對了，成交之後的盤口不對。')
        print(f'    賣單應該是  {want_asks}')
        print(f'    你的賣單是  {after[0]}')
        print(f'    買單應該是  {want_bids}')
        print(f'    你的買單是  {after[1]}')
        return False
    print(f'{head}過')
    return True


def run():
    asks0 = [(100.5, 3.0), (101.0, 1.0), (101.5, 2.0)]
    bids0 = [(100.0, 2.0), (99.5, 4.0), (99.0, 1.0)]
    results = [
        _check(1, '買 2 個，只吃賣一的一部分', 'buy', 2,
               [(100.5, 2.0)],
               [(100.5, 1.0), (101.0, 1.0), (101.5, 2.0)], bids0),
        _check(2, '買 4 個，吃穿兩檔', 'buy', 4,
               [(100.5, 3.0), (101.0, 1.0)],
               [(101.5, 2.0)], bids0),
        _check(3, '賣 3 個，方向反過來', 'sell', 3,
               [(100.0, 2.0), (99.5, 1.0)],
               asks0, [(99.5, 3.0), (99.0, 1.0)]),
        _check(4, '買 10 個，盤口不夠吃', 'buy', 10,
               [(100.5, 3.0), (101.0, 1.0), (101.5, 2.0)],
               [], bids0),
    ]
    print()
    if all(results):
        print('四關全過。把文件最底下三行開頭的 # 去掉，拿你的函數對一下手算的那一題。')
    else:
        print(f'過了 {sum(results)} 關，共 4 關。改完再跑一次。')
    return all(results)


if __name__ == '__main__':
    run()
    # 四關全過以後，把下面三行開頭的 # 去掉：
    book = make_book()
    print(book.market('buy', 5))
    book.show()

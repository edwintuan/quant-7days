"""引擎課 · 第二天：讓限價單也能成交

只要 Python 3，不用裝任何包。
跑法：python3 day2.py
你寫兩段：Book.limit 和 Book.cancel，都標著「你來寫」。

和第一天不一樣的三處：
  1. 價格和數量改成整數。價格以「最小跳動」為單位，10050 就是 100.50。
     理由：0.1 + 0.2 在電腦裏不等於 0.3，拿小數比價格大小，遲早比錯。
  2. 每一筆成交記成一個 Trade，寫明誰是 maker（先掛在盤口等的），誰是 taker（後來吃它的）。
  3. 單號由 Book 自己發，越早來的號越小。
"""
from dataclasses import dataclass


@dataclass
class Order:
    id: int
    side: str      # 'buy' 或 'sell'
    price: int     # 限價，整數
    qty: int       # 還沒成交的數量


@dataclass
class Trade:
    """ Just single transaction which been made, not a commission"""
    price: int     # 成交價
    qty: int
    maker_id: int  # 先掛在盤口裏等的那張單
    taker_id: int  # 後來吃它的那張單


class Book:
    def __init__(self):
        self.bids = []     # 買單，最好的排最前：價格高的先，同價先來的先
        self.asks = []     # 賣單，最好的排最前：價格低的先，同價先來的先
        self.trades = []   # 所有成交，按先後
        self._next_id = 0

    def _new_id(self):
        self._next_id += 1
        return self._next_id

    def _rest(self, order):
        """把一張單放進盤口裏它該排的位置。就是第一天的 add。
        名字前面加了底線，意思是它只給 Book 自己用：外面的人下單要走 limit。
        """
        if order.side == 'buy':
            self.bids.append(order)
            self.bids.sort(key=lambda o: (-o.price, o.id))
        else:
            self.asks.append(order)
            self.asks.sort(key=lambda o: (o.price, o.id))

    def limit(self, side, price, qty, ioc=False):
        """限價單。買單：最多肯付 price。賣單：最少要收 price。

        分兩步：
          1. 先看對面。只要對面最好的價「夠得著」，就成交，和市價單一樣一張一張吃，
             吃到數量夠了，或者對面的價夠不著了為止。
             成交價用盤口裏那張單的價（maker 的價），不是新來這張的價。
          2. 還有沒成交的，剩下的數量掛進盤口等（用 self._rest）。
        回傳這張單（Order）。它的 qty 要是還沒成交的數量；全部成交了就是 0，也不掛進盤口。

        記成交、扣數量、拿走吃光的單，都和上面的 market 一樣。
        """
        order = Order(self._new_id(), side, price, qty)
        # ---------- 你來寫 ----------
        book = self.asks if side == 'buy' else self.bids
        # Taker
        while order.qty > 0 and book:
            top = book[0]
            # Break the loop if price not in the limit
            if ((top.price > order.price) and side == 'buy') or ((top.price < order.price) and side == 'sell'): break
            take = min(top.qty, order.qty)
            self.trades.append(Trade(top.price, take, top.id, order.id))
            top.qty -= take
            order.qty -= take
            if top.qty == 0:
                book.pop(0)
        # Now we got remain order after it been a taker, next go to be a maker, but firstly check if the order.qty==0
        if order.qty == 0 or ioc:
            return order
        # Maker, if IOC no maker
        self._rest(order)
        # ----------------------------
        # So actually the return order show the final maker's qty and price, nothing about taker except Trades history
        return order

    def market(self, side, qty):
        return self.limit(side, float('inf') if side == 'buy' else 0, qty, ioc=True)

    def cancel(self, order_id):
        """撤單。盤口裏有這張單（買單、賣單兩邊都要找），就拿走，回傳 True；沒有就回傳 False。
        單號哪裏來：limit 回傳的那張單，它的 id 就是。
        """
        # ---------- 你來寫 ----------
        for book in (self.bids, self.asks):
            for o in book:
                if o.id == order_id:
                    book.remove(o)
                    return True

        # ----------------------------
        return False

    def show(self):
        """把盤口印出來：賣單在上，買單在下。"""
        for o in reversed(self.asks):
            print(f'  賣  {o.price:>7}  {o.qty:>4}    #{o.id}')
        print('  ' + '-' * 26)
        for o in self.bids:
            print(f'  買  {o.price:>7}  {o.qty:>4}    #{o.id}')


# ====================== 下面是測試，不用改 ======================

def make_book():
    """和第一天同一張盤口，價格乘了 100。單號 1 到 6。"""
    book = Book()
    for side, price, qty in [('sell', 10150, 2), ('sell', 10100, 1), ('sell', 10050, 3),
                             ('buy', 10000, 2), ('buy', 9950, 4), ('buy', 9900, 1)]:
        book._rest(Order(book._new_id(), side, price, qty))
    return book


def _levels(orders):
    return [(o.price, o.qty) for o in orders]


def _fail(head, msg, *pairs):
    print(f'{head}沒過：{msg}')
    for label, value in pairs:
        print(f'    {label}  {value}')
    return False


def _run(n, title, steps, want_trades, want_asks, want_bids, want_left):
    """從課上那張盤口開始，照 steps 下單，然後查成交、盤口、回傳的那張單。"""
    head = f'第 {n} 關（{title}）'
    book = make_book()
    start = (_levels(book.asks), _levels(book.bids))
    last = None
    try:
        for name, args in steps:
            last = getattr(book, name)(*args)
    except Exception as e:
        return _fail(head, f'報錯了，{type(e).__name__}: {e}')
    got = [(t.price, t.qty, t.maker_id) for t in book.trades]
    asks, bids = _levels(book.asks), _levels(book.bids)
    if not got and (asks, bids) == start:
        return _fail(head, '什麼都沒發生：這張單既沒成交，也沒掛進盤口。那一段還沒寫？')
    if bids and asks and bids[0][0] >= asks[0][0]:
        return _fail(head, f'盤口壞了：買一 {bids[0][0]} 沒有低於賣一 {asks[0][0]}。夠得著的單應該先成交，價格相等也算夠得著。')
    if got != want_trades:
        if got and [(q, m) for _, q, m in got] == [(q, m) for _, q, m in want_trades]:
            return _fail(head, '成交的對象和數量對了，成交價不對。成交價是盤口裏那張單的價。',
                         ('應該是', want_trades), ('你的是', got))
        return _fail(head, '成交不對。每筆是（成交價, 數量, maker 的單號）。',
                     ('應該是', want_trades), ('你的是', got))
    if any(q <= 0 for _, q in asks + bids):
        return _fail(head, '成交對了，可盤口裏留著數量是 0 的單。全部成交了的單不要掛進去。',
                     ('你的賣單是', asks), ('你的買單是', bids))
    if (asks, bids) != (want_asks, want_bids):
        return _fail(head, '成交對了，成交之後的盤口不對。',
                     ('賣單應該是', want_asks), ('你的賣單是', asks),
                     ('買單應該是', want_bids), ('你的買單是', bids))
    left = getattr(last, 'qty', None)
    if left != want_left:
        return _fail(head, f'成交和盤口都對，可回傳的那張單不對：它的 qty 應該是還沒成交的數量 {want_left}，你的是 {left}。')
    print(f'{head}過')
    return True


def _check_cancel(n):
    head = f'第 {n} 關（撤單）'
    book = make_book()
    start = (_levels(book.asks), _levels(book.bids))
    try:
        a = book.cancel(3)       # 賣一那張
        b = book.cancel(3)       # 已經撤掉了
        c = book.cancel(999)     # 從來沒有過
        d = book.cancel(5)       # 一張買單，排在中間
    except Exception as e:
        return _fail(head, f'報錯了，{type(e).__name__}: {e}')
    asks, bids = _levels(book.asks), _levels(book.bids)
    if (asks, bids) == start and not (a or b or c or d):
        return _fail(head, '什麼都沒撤掉。那一段還沒寫？')
    if asks != [(10100, 1), (10150, 2)]:
        return _fail(head, '撤掉 3 號（賣一那張）以後，賣單應該剩 [(10100, 1), (10150, 2)]。', ('你的賣單是', asks))
    if bids != [(10000, 2), (9900, 1)]:
        return _fail(head, '撤掉 5 號（中間那張買單）以後，買單應該剩 [(10000, 2), (9900, 1)]。', ('你的買單是', bids))
    if (a, b, c, d) != (True, False, False, True):
        return _fail(head, f'單撤對了，回傳值不對。撤 3 號、再撤 3 號、撤 999 號、撤 5 號，應該是 True、False、False、True，你的是 {a}、{b}、{c}、{d}。')
    print(f'{head}過')
    return True


_RANDOM_ANSWER = (2012, 3647, 36469526)   # 標準寫法跑出來的（筆數, 成交量, 成交額）


def _check_random(n):
    """亂下三千張限價單。每下一張，查四件任何時候都該成立的事。"""
    import random
    head = f'第 {n} 關（亂下三千張單，盤口不能壞）'
    rng = random.Random(7)
    book = Book()
    sent = traded = 0
    try:
        for step in range(1, 3001):
            side = rng.choice(['buy', 'sell'])
            qty = rng.randint(1, 5)
            price = 10000 + rng.randint(-30, 30)
            seen = len(book.trades)
            book.limit(side, price, qty)
            sent += qty
            if not (book.trades or book.bids or book.asks):
                return _fail(head, '第 1 張單下進去，什麼都沒發生。那一段還沒寫？')
            what = f"第 {step} 張單（{'買' if side == 'buy' else '賣'} {price}，{qty} 個）之後，"
            for t in book.trades[seen:]:
                traded += t.qty
                if (side == 'buy' and t.price > price) or (side == 'sell' and t.price < price):
                    return _fail(head, what + f'它有一筆成交在 {t.price}，比它自己的限價還差。')
            if book.bids and book.asks and book.bids[0].price >= book.asks[0].price:
                return _fail(head, what + f'買一 {book.bids[0].price} 沒有低於賣一 {book.asks[0].price}。')
            if any(o.qty <= 0 for o in book.bids + book.asks):
                return _fail(head, what + '盤口裏有數量不是正數的單。')
            resting = sum(o.qty for o in book.bids + book.asks)
            if sent != resting + 2 * traded:
                return _fail(head, what + f'數量對不上賬：送進來 {sent}，盤口裏 {resting}，成交 {traded}。'
                                          '每成交 1 個，買賣兩邊各少 1 個，所以應該是 送進來 ＝ 盤口裏 ＋ 2 × 成交。')
    except Exception as e:
        return _fail(head, f'報錯了，{type(e).__name__}: {e}')
    got = (len(book.trades), traded, sum(t.price * t.qty for t in book.trades))
    if not book.trades:
        return _fail(head, '三千張單，一筆成交都沒有。')
    if _RANDOM_ANSWER and got != _RANDOM_ANSWER:
        if got[:2] == _RANDOM_ANSWER[:2]:
            hint = '筆數和數量都對，成交額不對，那就是有的成交價不對。'
        elif got[1] == _RANDOM_ANSWER[1]:
            hint = '成交的數量對，筆數不對，多半是同一個價上沒有讓先來的先成交。'
        else:
            hint = '先把前面沒過的關修好。'
        return _fail(head, '盤口沒壞，賬也對得上，可成交和標準答案不一樣。' + hint,
                     ('應該是', '{} 筆，共 {} 個，成交額 {}'.format(*_RANDOM_ANSWER)),
                     ('你的是', '{} 筆，共 {} 個，成交額 {}'.format(*got)))
    print(f'{head}過，一共成交 {got[0]} 筆')
    return True


def run():
    asks0 = [(10050, 3), (10100, 1), (10150, 2)]
    bids0 = [(10000, 2), (9950, 4), (9900, 1)]
    results = [
        _run(1, '買價夠不著，掛進去等', [('limit', ('buy', 10020, 2))],
             [], asks0, [(10020, 2)] + bids0, 2),
        _run(2, '買價夠得著，按盤口裏的價成交', [('limit', ('buy', 10100, 4))],
             [(10050, 3, 3), (10100, 1, 2)], [(10150, 2)], bids0, 0),
        _run(3, '吃不完，剩下的掛進去', [('limit', ('buy', 10100, 6))],
             [(10050, 3, 3), (10100, 1, 2)], [(10150, 2)], [(10100, 2)] + bids0, 2),
        _run(4, '賣單也一樣，方向反過來', [('limit', ('sell', 9950, 8))],
             [(10000, 2, 4), (9950, 4, 5)], [(9950, 2)] + asks0, [(9900, 1)], 2),
        _run(5, '同一個價，先來的先成交',
             [('limit', ('sell', 10050, 2)), ('limit', ('buy', 10050, 4))],
             [(10050, 3, 3), (10050, 1, 7)], [(10050, 1), (10100, 1), (10150, 2)], bids0, 0),
        _check_cancel(6),
        _check_random(7),
    ]
    print()
    if all(results):
        print('七關全過。你的引擎現在能撮合了。')
        print('把文件最底下幾行開頭的 # 去掉，拿它對一下手算的那一題。')
    else:
        print(f'過了 {sum(results)} 關，共 7 關。改完再跑一次。')
    return all(results)


if __name__ == '__main__':
    run()
    # 七關全過以後，把下面幾行開頭的 # 去掉：
    book = make_book()
    order = book.limit('buy', 10100, 6)
    for t in book.trades:
        print(t)
    print('這張單還剩', order.qty, '個')
    book.show()

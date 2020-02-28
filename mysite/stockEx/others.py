from .models import Stock

stocks = Stock.objects.all()
class StockPurchaseInitial():
    def __init__(self):
        self.stocks = []
        for i in range (len(stocks)):
            self.stocks.append((stocks[i].get_company), 0)

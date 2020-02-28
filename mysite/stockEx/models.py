from django.db import models, migrations
from django.contrib.auth.models import User
import datetime, pytz, random
# Create your models here.
class UserData(models.Model):
    team = models.IntegerField()
    name = models.CharField(max_length = 20)
    cash = models.IntegerField(default = 5000)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def modify_cash(self, delta):
        self.cash += delta
        self.save()
    def get_cash(self):
        return int(self.cash)
 
class UserStockHolding(models.Model):
    company = models.CharField(max_length = 20)
    holdings = models.IntegerField()
    average_cost = models.IntegerField()
    total_cost = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def modify_holdings(self, new_holdings, price):
        if new_holdings > 0:
            self.total_cost = self.total_cost + new_holdings * price
            self.average_cost = (self.average_cost*self.holdings + new_holdings * price) / (self.holdings + new_holdings)
            self.holdings += new_holdings
        else: # sell out
            self.total_cost += new_holdings*self.average_cost
            self.holdings += new_holdings
        self.save()

    def compute_market_value(self, price):
        return (self.holdings * price)
    def get_average_cost(self):
        return int(self.average_cost)
    def get_holdings(self):
        return int(self.holdings)
    def get_company(self):
        return self.company

class GameSetting(models.Model):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    interval = models.IntegerField()
    reload_time = models.DateTimeField()
    def get_start_time(self):
        return (self.start_time)
    def get_end_time(self):
        return (self.end_time)
    def get_interval(self):
        return int(self.interval)
    def get_reload_time(self):
            return self.reload_time.astimezone(pytz.timezone('Asia/Taipei'))
    def js_get_reload_time(self):
        tz = pytz.timezone('Asia/Taipei')
        reload_time = self.reload_time.astimezone(pytz.timezone('Asia/Taipei'))
        return (reload_time.hour, reload_time.minute, reload_time.second)
    def game_is_ended(self):
        end_time = self.end_time.astimezone(pytz.timezone('Asia/Taipei'))
        now = datetime.datetime.now().astimezone(pytz.timezone('Asia/Taipei'))
        if end_time > now:
            return False
        return True
    def modify_end_time(self, new):
        self.end_time = new
        self.save()
    def modify_interval(self, new):
        self.reload_time = self.reload_time + datetime.timedelta(0, minutes = (new -self.interval))
        self.interval = new
        self.save() 
    def check_reload_time(self):
        now = datetime.datetime.now().astimezone(pytz.timezone('Asia/Taipei'))
        reload_time = self.reload_time.astimezone(pytz.timezone('Asia/Taipei'))
        if now > reload_time: # 如果已經更新過了
            # update Stock datas
            for stock in Stock.objects.all():
                stock.update_data(reload_time)
                stock.save()
            # update reload_time
            next_reload_time = reload_time
            while next_reload_time < now:
                next_reload_time += datetime.timedelta(0, minutes = self.interval)
            end_time = self.end_time.astimezone(pytz.timezone('Asia/Taipei'))
            if next_reload_time <= end_time:
                self.reload_time = next_reload_time
            else:
                self.reload_time.replace(hour = 0, minute = 0, second = 0)
            self.save()
        return self.reload_time
    
class Stock(models.Model):
    # with current price
    stock_symbol = models.IntegerField()# 不改變
    company = models.CharField(max_length = 20)# 不改變
    date_time = models.DateTimeField()
    price = models.IntegerField()
    growth_rate = models.FloatField()
    volume = models.IntegerField(default = 0) # 成交量

    def get_company(self):
        return self.company
    def get_price(self):
        return int(self.price)
    def get_date_time(self):
        return self.date_time
    def start_settings(self, start_time):#修改date_time as start time
        self.date_time = start_time
        self.save()
    def update_data(self, date_time):
        # 儲存歷史資料
        HistStockData.objects.create(date_time = self.date_time, volume = self.volume,
                            price = self.price, growth_rate = self.growth_rate, stock = self)
        # 更新價格、時間
        growth_rate = random.normalvariate(0, 1/3)
        while (growth_rate > 0.4 or growth_rate < -0.35):#設定上下限 避免過度極端
            growth_rate = random.normalvariate(0, 1/3)
        self.price = self.price * (1+growth_rate)
        self.growth_rate = round(growth_rate, 4)
        self.date_time = date_time




class HistStockData(models.Model):
    date_time = models.DateTimeField()
    price = models.IntegerField()
    growth_rate = models.FloatField()
    volume = models.IntegerField(default = 0) # 成交量
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)

class TransactionRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_time = models.DateTimeField()
    company = models.CharField(max_length = 20)
    quantity = models.IntegerField()#數量
    amount = models.IntegerField()#總金額

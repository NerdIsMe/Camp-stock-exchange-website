from django.db import models, migrations
from django.conf import settings
from django.contrib.auth.models import User
import datetime, pytz, random, os, matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
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
    stock_symbol = models.IntegerField()
    company = models.CharField(max_length = 20)
    holdings = models.IntegerField()
    average_cost = models.FloatField()
    total_cost = models.FloatField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def modify_holdings(self, new_holdings, price):
        if new_holdings > 0:
            self.total_cost = self.total_cost + new_holdings * price
            self.average_cost = (self.average_cost*self.holdings + new_holdings * price) / (self.holdings + new_holdings)
            self.average_cost = round(self.average_cost, 2)
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
            # update Stock datas & draw new plot
            for stock in Stock.objects.all():
                stock.update_data(reload_time)
                stock.draw_new_plot()
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
    def get_symbol(self):
        return self.stock_symbol
    def start_settings(self, start_time):#修改date_time as start time
        self.price = 0
        self.date_time = start_time
        self.save()
    
    def update_data(self, date_time):
        # 儲存歷史資料
        if date_time != self.date_time: # 不是遊戲開始的瞬間 才要儲存歷史股價
            HistStockData.objects.create(date_time = self.date_time, volume = self.volume,
                            price = self.price, growth_rate = self.growth_rate, stock = self)
        else:# 遊戲開始的瞬間，要給予股票初始價格
            self.price = random.randint(50, 800)
        # 更新價格、時間
        growth_rate = random.normalvariate(0, 1/3)
        while (growth_rate > 0.4 or growth_rate < -0.35):#設定上下限 避免過度極端
            growth_rate = random.normalvariate(0, 1/3)
        self.price = self.price * (1+growth_rate)
        self.growth_rate = round(growth_rate, 4)
        self.date_time = date_time

    def draw_new_plot(self):
        matplotlib.rcParams['timezone'] = 'Asia/Taipei'
        prices = []
        growth_rates = []
        dates = [] 
        # get history data
        for i in self.histstockdata_set.all():
            prices.append(int(i.get_price()))
            growth_rates.append(i.get_growth_rate())
            dates.append(i.get_date_time().astimezone(pytz.timezone('Asia/Taipei')))
        # get current data
        prices.append(self.price)
        growth_rates.append(self.growth_rate)
        dates.append(self.date_time.astimezone(pytz.timezone('Asia/Taipei')))

        # 格式化刻度单位
        interval = GameSetting.objects.last().get_interval()
        hours = mdates.HourLocator(tz = pytz.timezone('Asia/Taipei'))
        minutes = mdates.MinuteLocator(interval=interval, tz = pytz.timezone('Asia/Taipei'))
        seconds = mdates.SecondLocator(tz = pytz.timezone('Asia/Taipei'))

        # dateFmt = mdates.DateFormatter('%Y-%m-%d %H:%M')
        # dateFmt = mdates.DateFormatter('%Y-%m-%d')
        dateFmt = mdates.DateFormatter('%H:%M', tz = pytz.timezone('Asia/Taipei'))  # 显示格式化后的结果

        fig, ax = plt.subplots()    # 获得设置方法
        # format the ticks
        ax.xaxis.set_major_locator(minutes)  # 设置主要刻度
        #ax.xaxis.set_minor_locator(minutes)  # 设置次要刻度
        ax.xaxis.set_major_formatter(dateFmt)  # 刻度标志格式

        # 添加图片数据
        plt.plot_date(dates, prices, '-', marker='.', tz = pytz.timezone('Asia/Taipei'))
        i = 0
        for x,y in zip(dates, prices):
            label =str("{:.2f}".format(y)) + ' \n(' + str(round(growth_rates[i]*100, 2)) + '%)'
            i += 1
            plt.annotate(label, # this is the text
                        (x,y), # this is the point to label
                        textcoords="offset points", # how to position the text
                        xytext=(0,10), # distance from text to points (x,y)
                        ha='center') # horizontal alignment can be left, right or center

        delta = datetime.timedelta(0, minutes= interval)
        ax.set_xlim([dates[0] - delta, dates[-1] + delta])
        #plt.gca().xaxis_date('Asia/Taipei')
        #fig.autofmt_xdate()  # 自动格式化显示方式
        plt.xticks(rotation = 90)
        plt.ylabel('價格')
        plt.xlabel('時間')
        address = 'static/images/' + str(self.stock_symbol) + '.png'
        plt.savefig(os.path.join(settings.BASE_DIR, address))  # 儲存圖片

class HistStockData(models.Model):
    date_time = models.DateTimeField()
    price = models.IntegerField()
    growth_rate = models.FloatField()
    volume = models.IntegerField(default = 0) # 成交量
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)

    def get_price(self):
        return self.price
    def get_growth_rate(self):
        return self.growth_rate
    def get_date_time(self):
        return self.date_time

class TransactionRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_time = models.DateTimeField()
    company = models.CharField(max_length = 20)
    quantity = models.IntegerField()#數量
    amount = models.IntegerField()#總金額

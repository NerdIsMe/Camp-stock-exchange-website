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
    cash = models.FloatField(default = 0)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def modify_cash(self, delta):
        self.cash += delta
        self.save()
    def get_cash(self):
        return round(float(self.cash), 2)
 
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
        return round((self.holdings * price), 2)
    def get_average_cost(self):
        return round(self.average_cost, 2)
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
    def js_get_reload_time(self, is_superuser):
        tz = pytz.timezone('Asia/Taipei')
        reload_time = self.reload_time.astimezone(pytz.timezone('Asia/Taipei'))
        if is_superuser:
            delta = datetime.timedelta(0, seconds=2)
            reload_time = reload_time - delta
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
        # 提早2秒鐘更新股價
        delta = datetime.timedelta(0, seconds=2)
        if now > (reload_time-delta): # 如果已經要更新了
            # update Stock datas & draw new plot
            for stock in Stock.objects.all():
                stock.update_data(reload_time)
                #stock.draw_new_plot() 改為第一個點進去的人材重新畫
                stock.save()
            # update reload_time
            next_reload_time = reload_time
            while (next_reload_time-delta) < now:
                next_reload_time += datetime.timedelta(0, minutes = self.interval)
            end_time = self.end_time.astimezone(pytz.timezone('Asia/Taipei'))
            if next_reload_time <= end_time:
                self.reload_time = next_reload_time
            else:
                self.reload_time.replace(hour = 0, minute = 0, second = 0)
            self.save()
    
class Stock(models.Model):
    # with current price
    stock_symbol = models.IntegerField()# 不改變
    company = models.CharField(max_length = 20)# 不改變
    date_time = models.DateTimeField()
    price = models.FloatField()
    growth_rate = models.FloatField()
    volume = models.IntegerField(default = 0) # 成交量
    img_roload_time = models.DateTimeField()

    def get_company(self):
        return self.company
    def get_price(self):
        return float(self.price)
    def get_date_time(self):
        return self.date_time
    def get_symbol(self):
        return self.stock_symbol
    def start_settings(self, start_time):#修改date_time as start time
        self.price = 0
        self.growth_rate = 0
        self.date_time = start_time
        self.img_roload_time = start_time
        self.save()

    def update_data(self, date_time):
        # 儲存歷史資料
        if date_time != self.date_time: # 不是遊戲開始的瞬間 才要儲存歷史股價
            HistStockData.objects.create(date_time = self.date_time, volume = self.volume,
                            price = self.price, growth_rate = self.growth_rate, stock = self)
        else:# 遊戲開始的瞬間，要給予股票初始價格
            self.price = float(random.randint(30, 700))
            return
        # 更新價格、時間
        growth_rate = random.normalvariate(0, 1/3)
        while (growth_rate > 0.4 or growth_rate < -0.35):#設定上下限 避免過度極端
            growth_rate = random.normalvariate(0, 1/3)
        self.price = round(self.price * (1+growth_rate), 2)
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
        minutes = mdates.MinuteLocator(interval=10, tz = pytz.timezone('Asia/Taipei'))
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
        plt.plot_date(dates, prices, '-', marker='', linewidth = 1.2, color = '#02a33d')
        '''
        i = 0
        for x,y in zip(dates, prices):
            label =str("{:.2f}".format(y)) + ' \n(' + str(round(growth_rates[i]*100, 2)) + '%)'
            i += 1
            plt.annotate(label, # this is the text
                        (x,y), # this is the point to label
                        textcoords="offset points", # how to position the text
                        xytext=(0,10), # distance from text to points (x,y)
                        ha='center') # horizontal alignment can be left, right or center
        '''
        if len(prices) >= 3:
            # 最大值：
            max_price = max(prices)
            label = 'Max: '+str("{:.2f}".format(max_price))# + ' \n(' + str(round(growth_rates[-1]*100, 2)) + '%)'
            max_index = prices.index(max_price)
            plt.annotate(label, # this is the text
                            (dates[max_index], max_price), # this is the point to label
                            textcoords="offset points", # how to position the text
                            xytext=(0,10), # distance from text to points (x,y)
                            ha='center', # horizontal alignment can be left, right or center
                            color='r')
            #plt.scatter(dates[max_index], max_price,color = 'r')
            # 最小值：
            min_price = min(prices)
            label = 'Min: '+str("{:.2f}".format(min_price))# + ' \n(' + str(round(growth_rates[-1]*100, 2)) + '%)'
            min_index = prices.index(min_price)
            plt.annotate(label, # this is the text
                            (dates[min_index], min_price), # this is the point to label
                            textcoords="offset points", # how to position the text
                            xytext=(0,-10), # distance from text to points (x,y)
                            ha='center', # horizontal alignment can be left, right or center
                            color='b')
            #plt.scatter(dates[min_index], min_price,color = 'b')
        if len(prices) < 3 or (self.price != max(prices) and self.price != min(prices)):
            label = 'Current: \n'+str("{:.2f}".format(prices[-1]))# + ' \n(' + str(round(growth_rates[-1]*100, 2)) + '%)'
            plt.annotate(label, # this is the text
                            (dates[-1], prices[-1]), # this is the point to label
                            textcoords="offset points", # how to position the text
                            xytext=(15,10), # distance from text to points (x,y)
                            ha='center', # horizontal alignment can be left, right or center
                            )
        delta = datetime.timedelta(0, minutes= interval)
        ax.set_xlim([dates[0] - delta, dates[-1] + delta])
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        #plt.gca().xaxis_date('Asia/Taipei')
        #fig.autofmt_xdate()  # 自动格式化显示方式
        plt.xticks(rotation = 90)
        plt.ylabel('Price')
        plt.xlabel('Time')
        plt.scatter(dates[-1], prices[-1],color = '#02a33d')
        address = 'static/images/' + str(self.stock_symbol) + '.png'
        plt.savefig(os.path.join(settings.BASE_DIR, address), dpi = 300)  # 儲存圖片
        plt.close()

    def check_img(self):
        reload_time = self.img_roload_time.astimezone(pytz.timezone('Asia/Taipei'))
        now = datetime.datetime.now().astimezone(pytz.timezone('Asia/Taipei'))
        if  reload_time < now: #要更新圖片了
            self.img_roload_time = GameSetting.objects.last().get_reload_time()
            self.draw_new_plot()
            self.save()

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

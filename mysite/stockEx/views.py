from django.shortcuts import render
from django.http import HttpResponseRedirect
from .forms import LoginForm, RegisterForm, GameResetForm, GameSettingForm, StockPurchaseForm
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from .models import *

import datetime
import pytz
def to_datetime(s):
    s = s.split('-')
    year = int(s[0])
    mon = int(s[1])
    s = s[2].split('T')
    day = int(s[0])
    s = s[1].split(':')
    h = int(s[0])
    m = int(s[1])
    tz = pytz.timezone('Asia/Taipei')
    time = datetime.datetime(year, mon, day, h, m)
    time_tz = tz.localize(time)
    return time_tz

def do_compute(amount, price, cash, type):
    '''
    compute = ['-' for i in range(len(stocks))]
    ss = [('s'+str(i+1)) for i in range(len(stocks))]
    for i in range(len(stocks)):
        tempt = stock_purchase[ss[i]].value()
        s = int(tempt)
        if s != 0:
            price = int(stocks[i].get_price())
            total = s * price
            compute[i] = str(s) + '(張) x ' + str(price) + '(元) = ' + str(total) + '元'
    '''
    if type == 'buy':
        total = amount * price
        after_cash = cash - total
        compute = '支出：' + str(amount) + '(張) x ' + str(price) + '(元) = 共' + str(total) + '元'
        cash_compute = '現金餘額：' + str(cash) + "元 → " + str(after_cash) + '元'
    elif type == 'sell':
        total = amount * price
        after_cash = cash + total
        compute = '獲得：' + str(amount) + '(張) x ' + str(price) + '(元) = 共' + str(total) + '元'
        cash_compute = '銀行帳戶餘額：' + str(cash) + "元 → " + str(after_cash) + '元'
    return (compute, cash_compute)

def compute_total(amount, price):
    '''
    ss = [('s'+str(i+1)) for i in range(len(stocks))]
    total = 0
    for i in range (0, len(stocks)):
        total += int(stock_purchase[ss[i]].value()) * stocks[i].get_price()
    '''
    total = amount * price
    return total

# Create your views here.
def home(request):
    date = datetime.datetime.now().astimezone(pytz.timezone('Asia/Taipei')).strftime("%Y/%m/%d %H:%M:%S")
    stocks = Stock.objects.all()

    # 設定網頁自動更新時間 每個跟股價有關的 之後都要放上去
    (h, m, s) = (0, 0, 0)
    game_settings = GameSetting.objects.all()
    if len(game_settings) != 0: #已經有遊戲設定
        cur_settings = GameSetting.objects.last()
        if not cur_settings.game_is_ended():#遊戲尚未結束
            cur_settings.check_reload_time() # 檢查下次更新時間
            (h, m, s) = cur_settings.js_get_reload_time()

    return render(request, 'stockEx/index.html', locals())

def stock_info(request, stock_symbol):
    is_login = False
    compute = False
    stock = Stock.objects.get(stock_symbol = stock_symbol)
    price = stock.get_price()
    date_time = stock.get_date_time().astimezone(pytz.timezone('Asia/Taipei')).strftime("%Y/%m/%d %H:%M:%S")
    amount = 0
    do_modify = False
    img_location = "images/" + str(stock.get_symbol()) + ".png"
    if request.user.is_authenticated:# 登入的情況下
        is_login = True
        user_data = UserData.objects.get(user = request.user)
        is_hold = False
        tempt = UserStockHolding.objects.filter(user = request.user, company = stock.get_company())
        cur_deposit = user_data.get_cash()
        if len(tempt) != 0: #擁有股票
            is_hold = True
            holdings = tempt[0]
            market_value = holdings.compute_market_value(price)
            delta = price - holdings.get_average_cost()
        
        #收到request
        if request.method == 'POST':
            amount = int(request.POST['amount'])# amount 是張數
            cash = user_data.get_cash()
            compute = True
            if 'buy' in request.POST:
                (computation, cash_compute) = do_compute(amount, price, cash, 'buy')
                if cur_deposit < compute_total(amount, price):
                    not_enough_cash = True
                buy = True
            elif 'sell' in request.POST:
                not_enough_holdings = True
                if len(tempt) != 0:#擁有股票
                    if amount <= holdings.get_holdings():#足夠張數可以賣
                        (computation, cash_compute) = do_compute(amount, price, cash, 'sell')
                        not_enough_holdings = False
                sell = True
            elif 'buy_modify' in request.POST:
                do_modify = True
                compute = False
                (computation, cash_compute) = do_compute(amount, price, cash, 'buy')
            elif 'sell_modify' in request.POST:
                do_modify = True
                compute = False

            elif 'buy_confirmed' in request.POST:# 確認購買
                compute = False
                total_amount = compute_total(amount, price)
                user_data.modify_cash(-total_amount)#現金減少
                user_data.save()
                if len(tempt) != 0: #先前有持有股票
                    holdings.modify_holdings(amount, price)
                    holdings.save()
                else:#先前沒買過股票
                    holdings = UserStockHolding.objects.create(user = request.user, average_cost = price,
                                    company = stock.get_company(), holdings = amount, 
                                    stock_symbol = stock.get_symbol(), total_cost = price * amount)
                    is_hold = True
                # upadate 資料
                holdings = UserStockHolding.objects.get(user = request.user, company = stock.get_company())
                market_value = holdings.compute_market_value(price)
                delta = price - holdings.get_average_cost()
                cur_deposit = user_data.get_cash()

            elif 'sell_confirmed' in request.POST:# 確認賣出
                compute = False
                total_amount = compute_total(amount, price)
                user_data.modify_cash(total_amount)#現金增加
                user_data.save()
                holdings.modify_holdings(-amount, price)
                holdings.save()
                if holdings.get_holdings() == 0: #賣完後，未持有股票
                    holdings.delete()
                    is_hold = False
                # upadate 資料
                market_value = holdings.compute_market_value(price)
                delta = price - holdings.get_average_cost()
                cur_deposit = user_data.get_cash()
    return render(request, 'stockEx/stock_info.html', locals())

@login_required
def personal_data(request):
    user_data = UserData.objects.get(user = request.user)
    user = User.objects.get(username = request.user)
    stocks_market_value = 0

    #計算股票市值
    user_stocks = user.userstockholding_set.all()
    if len(user_stocks) != 0: #擁有股票
        stock_prices = []
        delta = []
        market_value = []
        for i in user_stocks:
            price = Stock.objects.get(company = i.get_company()).get_price()
            stock_prices.append(price)
            delta.append(price - i.get_average_cost())
            market_value.append(i.compute_market_value(price))
            stocks_market_value += i.compute_market_value(price)
        user_stocks = zip(user_stocks, stock_prices, delta, market_value)
    total_assets = stocks_market_value + user_data.get_cash()
    return render(request, 'stockEx/personal_data.html', locals())
    
def login(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('/home/')

    login_failed = False
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form["username"].value()
            password = form["password"].value()
            user = auth.authenticate(username = username, password = password)
            if user != None and user.is_active:
                auth.login(request, user)

                return HttpResponseRedirect('/home/')
            else:
                login_failed = True
    else:
        form = LoginForm()
    return render(request, 'stockEx/login.html', locals())

@login_required
def logout(request):
    auth.logout(request)
    return render(request, 'stockEx/logout.html', locals())

def register(request):
    if request.method == 'POST':
        new_user = UserCreationForm(request.POST)
        user_data = RegisterForm(request.POST)
        if new_user.is_valid() and user_data.is_valid():
            # 註冊帳戶
            new_user = new_user.save()
            # 儲存個資
            team = user_data['team'].value()
            name = user_data['name'].value()
            UserData.objects.create(team = team, name = name, user = new_user)
            return HttpResponseRedirect('/home/')
    else:
        new_user = UserCreationForm()
        user_data = RegisterForm()
    return render(request, 'stockEx/register.html', locals())

@login_required
def gamereset(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/home/')

    is_setted = True
    # superuser
    #收到 request
    if request.method == 'POST':
        form = GameResetForm(request.POST)
        
        if form.is_valid() and 'start_time' in request.POST:
            GameSetting.objects.all().delete()
            start_time = to_datetime(request.POST['start_time'])
            interval = int(form['interval'].value())
            span = form['span'].value()
            end_time = start_time + datetime.timedelta(0, minutes = int(span))
            #reload_time = start_time + datetime.timedelta(0, minutes = interval)
            GameSetting.objects.create(start_time = start_time, end_time = end_time,
                                            interval = interval, reload_time = start_time)
            stocks = Stock.objects.all()
            for stock in stocks:
                    stock.start_settings(start_time)# 設定開始時間以及股價歸零
                    stock.save()
            HistStockData.objects.all().delete()
            return HttpResponseRedirect('/home/game_status/')
    #沒收到
    form = GameResetForm()
    return render(request, 'stockEx/game_reset.html', locals())

@login_required
def gamestatus(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/home/')   

    is_setted = True
    if len(GameSetting.objects.all()) == 0:
        is_setted = False
    else:
        cur = GameSetting.objects.last()
        cur_start_time = cur.get_start_time()
        cur_end_time = cur.get_end_time()
        cur_span = cur_end_time - cur_start_time
        cur_interval = cur.get_interval()
        
        now = datetime.datetime.now(tz=pytz.timezone('Asia/Taipei'))

        if  cur_start_time > now:
            g_status = 0
        elif cur_start_time < now and cur_end_time > now: #進行中
            g_status = 1 
        else:
            g_status = 2
        cur_start_time = cur.get_start_time().astimezone(pytz.timezone('Asia/Taipei')).strftime("%Y/%m/%d %H:%M:%S")
        cur_end_time = cur.get_end_time().astimezone(pytz.timezone('Asia/Taipei')).strftime("%Y/%m/%d %H:%M:%S")
    js = 'stockEx/javascript.js'
    return render(request, 'stockEx/game_status.html', locals())

@login_required
def gamesettings(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/home/')   
    if request.method == 'POST':
        form = GameSettingForm(request.POST)
        if form.is_valid():
            new_end_time = to_datetime(request.POST['end_time'])
            new_set = GameSetting.objects.last()
            new_set.modify_end_time(new_end_time)
            new_set.modify_interval(int(form['interval'].value()))
            new_set.save()
            return HttpResponseRedirect('../')
    end_time = GameSetting.objects.last().get_end_time().astimezone(pytz.timezone('Asia/Taipei')).strftime("%Y-%m-%dT%H:%M")
    start_time = GameSetting.objects.last().get_start_time().astimezone(pytz.timezone('Asia/Taipei')).strftime("%Y/%m/%d %H:%M:%S")
    interval = GameSetting.objects.last().get_interval()
    form = GameSettingForm()
    return render(request, 'stockEx/game_settings.html', locals())


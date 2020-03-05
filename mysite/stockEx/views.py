from django.shortcuts import render
from django.http import HttpResponseRedirect
from .forms import LoginForm, RegisterForm, GameResetForm, GameSettingForm, StockPurchaseForm, DepositForm
from django.contrib import auth
from django.contrib.auth.models import User
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
    if type == 'buy':
        total = round(amount * price, 2)
        after_cash = round(cash - total, 2)
        compute = '支出：' + str(amount) + '(張) x ' + str(price) + '(元) = 共' + str(total) + '元'
        cash_compute = '現金餘額：' + str(cash) + "元 → " + str(after_cash) + '元'
    elif type == 'sell':
        total = round(amount * price, 2)
        after_cash = round(cash + total, 2)
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
    total = round(amount * price, 2)
    return total

def get_reload_time(is_superuser=False):
    (h, m, s) = (0, 0, 0)
    game_settings = GameSetting.objects.all()
    if len(game_settings) != 0: #已經有遊戲設定
        cur_settings = GameSetting.objects.last()
        if not cur_settings.game_is_ended():#遊戲尚未結束
            if is_superuser:
                cur_settings.check_reload_time() # only super user檢查下次更新時間，避免太多人同時刷新股價 會出錯
                (h, m, s) = cur_settings.js_get_reload_time(is_superuser=True)
            else:
                (h, m, s) = cur_settings.js_get_reload_time(is_superuser)
    return (h, m, s)

# Create your views here.
def home(request):
    return render(request, 'stockEx/index.html', locals())

def stocks(request):
    date = datetime.datetime.now().astimezone(pytz.timezone('Asia/Taipei')).strftime("%Y/%m/%d %H:%M:%S")
    stocks = Stock.objects.all()
    
    is_positive = []
    deltas = []
    growth_rates = []
    for i in stocks:
        # 單股變化量
        delta = round(i.price - i.price/(1+i.growth_rate), 2)
        growth_rates.append(str(abs(round(i.growth_rate*100, 2))) + '%')
        if i.growth_rate < 0:
            is_positive.append(False)
        else:
            is_positive.append(True)
            delta = '+' + str(delta)
        deltas.append(delta)

    # 設定網頁自動更新時間
    (h, m, s) = get_reload_time()
    stocks = zip(is_positive, deltas, growth_rates, stocks)
    return render(request, 'stockEx/stocks.html', locals())

def stock_info(request, stock_symbol):
    # 設定網頁自動更新時間 每個跟股價有關的 之後都要放上去
    (h, m, s) = get_reload_time()
    #is_login = False, do_modify = False, compute = False
    stock = Stock.objects.get(stock_symbol = stock_symbol)
    price = stock.get_price()
    date_time = stock.get_date_time().astimezone(pytz.timezone('Asia/Taipei')).strftime("%Y/%m/%d %H:%M:%S")
    amount = 0
    # image
    img_location = "images/" + str(stock.get_symbol()) + ".png"
    stock.check_img()# 確認圖畫出來了沒

    if request.user.is_superuser:
        if 'plot' in request.POST:#管理員有權使網頁重新繪圖
            stock.draw_new_plot()
        return render(request, 'stockEx/stock_info.html', locals())

    if request.user.is_authenticated:# 一般使用者登入
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
                ''' upadate 資料
                holdings = UserStockHolding.objects.get(user = request.user, company = stock.get_company())
                market_value = holdings.compute_market_value(price)
                delta = round(price - holdings.get_average_cost(),2)
                cur_deposit = user_data.get_cash()
                '''
                cur = '/home/stocks/' + str(stock.get_symbol())
                return HttpResponseRedirect(cur)

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
                ''' upadate 資料
                market_value = holdings.compute_market_value(price)
                delta = round(price - holdings.get_average_cost(), 2)
                cur_deposit = user_data.get_cash()
                '''
                cur = '/home/stocks/' + str(stock.get_symbol())
                return HttpResponseRedirect(cur)
    return render(request, 'stockEx/stock_info.html', locals())

@login_required
def personal_data(request):
    user_data = UserData.objects.get(user = request.user)
    user = User.objects.get(username = request.user)
    stocks_market_value = 0
    #網頁更新時間
    (h, m, s) = get_reload_time()
    #計算股票市值
    user_stocks = user.userstockholding_set.all()
    if len(user_stocks) != 0: #擁有股票
        stock_prices = []
        is_positive = []
        deltas = []
        market_values = []
        for i in user_stocks:
            price = Stock.objects.get(company = i.get_company()).get_price()
            stock_prices.append(price)# 股價
            delta = price - i.get_average_cost()
            if delta < 0:
                is_positive.append(False)
            else:
                is_positive.append(True)
            deltas.append(abs(delta)) #平均成本-股價 價差
            market_values.append(i.compute_market_value(price))#持有股票市值
            stocks_market_value += i.compute_market_value(price)
        user_stocks = zip(user_stocks, stock_prices, is_positive, deltas, market_values)
    total_assets = stocks_market_value + user_data.get_cash()
    return render(request, 'stockEx/personal_data.html', locals())
    
def login(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('/home/')
    # 登入
    elif 'login' in request.POST:
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
    #reload page
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
                    stock.start_settings(start_time)# 設定開始時間、圖片重畫時間、股價歸零
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

# 股價更新以這個網頁為主
@login_required
def update_stock(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/home/')
    (h, m, s) = get_reload_time(is_superuser = True)
    return render(request, 'stockEx/update_stock.html', locals())

@login_required
def search_userdata(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/home/')
    # 查詢帳戶資料：
    if 'chinese_name' in request.GET:
        searched = True
        name = request.GET['chinese_name']
        user_data = UserData.objects.filter(name__contains = name)
    
    return render(request, 'stockEx/search_userdata.html', locals())

@login_required
def modify_deposit(request, username):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/home/')

    user_data = UserData.objects.get(user = User.objects.get(username=username))
    if request.method == 'POST':
        form = DepositForm(request.POST)
        amount = int(form['amount'].value())
        submitted = True
        if form.is_valid:
            if form['choice_type'].value() == 'save':# 選擇存款
                user_data.modify_cash(amount)
                msg = "你已成功存入" + str(amount) + '元'
            else:# 選擇題款
                if user_data.get_cash() < amount: #不夠錢提款
                    not_enough_deposit = True
                    msg = "銀行金額不足，無法領取" + str(amount) + '元'
                else:#可以提款
                    user_data.modify_cash(-amount)
                    msg = "你已成功提領" + str(amount) + '元'
            user_data.save()
            
    form = DepositForm()
    return render(request, 'stockEx/modify_deposit.html', locals())
    


    

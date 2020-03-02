from django import forms
from.models import GameSetting, Stock
TEAM_CHOICES = [
    (1, '一'), (2, '二'), (3, '三'), (4, '四'),(5, '五'),
    (6, '六'), (7, '七'), (8, '八'), (9, '九'), (10, '十'),
]
INTERVAL_CHOICES = [
     (1, '1'), (5, '5'), (10, '10'), (12, '12'), (15, '15'), (20, '20'), 
    (25, '25'), (30, '30')
]
DEPOSIT_CHOICES = [
    ('save', '存款'), ('withdrawal', '提款')
]

class LoginForm(forms.Form):
    username = forms.CharField(max_length = 30)
    password = forms.CharField(widget=forms.PasswordInput())

class RegisterForm(forms.Form):
    team = forms.ChoiceField(choices = TEAM_CHOICES)
    name = forms.CharField(max_length = 20)

class GameResetForm(forms.Form):
    interval = forms.ChoiceField(choices = INTERVAL_CHOICES)
    span = forms.IntegerField(min_value = 0, initial=120)
    game_pause = forms.BooleanField(required = False)
    terminate = forms.BooleanField(required = False)

class GameSettingForm(forms.Form):
    interval = forms.ChoiceField(choices = INTERVAL_CHOICES, initial = (400, '400'))
    
class StockPurchaseForm(forms.Form):
    s1 = forms.IntegerField(min_value = 0, initial = 0)
    s2 = forms.IntegerField(min_value = 0, initial = 0)
    s3 = forms.IntegerField(min_value = 0, initial = 0)
    s4 = forms.IntegerField(min_value = 0, initial = 0)
    s5 = forms.IntegerField(min_value = 0, initial = 0)
    s6 = forms.IntegerField(min_value = 0, initial = 0)
    s7 = forms.IntegerField(min_value = 0, initial = 0)
    s8 = forms.IntegerField(min_value = 0, initial = 0)
    s9 = forms.IntegerField(min_value = 0, initial = 0)
    s10 = forms.IntegerField(min_value = 0, initial = 0)

class DepositForm(forms.Form):
    choice_type = forms.ChoiceField(choices= DEPOSIT_CHOICES)
    amount = forms.IntegerField(min_value = 0)

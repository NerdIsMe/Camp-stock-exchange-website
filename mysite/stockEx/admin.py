from django.contrib import admin
from .models import UserData, GameSetting, Stock, HistStockData, TransactionRecord, UserStockHolding
# Register your models here.

class UserDataAdmin(admin.ModelAdmin):
    list_display = ('name', 'team', 'user', 'cash')
    list_filter = ('team',)
    search_fields = ('name','user__username', )

class GameSettingAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'reload_time', 'end_time', 'interval')

class StockAdmin(admin.ModelAdmin):
    list_display = ('stock_symbol', 'company', 'date_time', 'price', 'growth_rate', "volume")

class HistStockDataAdmin(admin.ModelAdmin):
    def get_company(self, obj):
        return obj.stock.company
    get_company.admin_order_field  = 'stock'  #准许排序
    list_display = ('date_time', 'get_company', 'price', 'growth_rate', 'volume')
    list_filter = ('date_time',)
    get_company.short_description = '公司'  # 修改表頭名稱
    search_fields = ('stock__company', )

class TransactionRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_time', 'amount')

class UserStockHoldingAdmin(admin.ModelAdmin):
    list_display = ('user', 'stock_symbol', 'company', 'holdings', 'average_cost', 'total_cost')
    search_fields = ['user__username',]


admin.site.register(UserData, UserDataAdmin)
admin.site.register(GameSetting, GameSettingAdmin)
admin.site.register(Stock, StockAdmin)
admin.site.register(HistStockData, HistStockDataAdmin)
admin.site.register(TransactionRecord, TransactionRecordAdmin)
admin.site.register(UserStockHolding, UserStockHoldingAdmin)
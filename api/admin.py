from django.contrib import admin
from .models import (
    ProductImageModel, 
    ProductModel, 
    ProductDetailModel, 
    FormModel,
    ProductPositionModel,
    TransactionModel
)

class ProductDetailsInline(admin.StackedInline):
    model = ProductDetailModel

@admin.register(ProductModel)
class ProductModelAdmin(admin.ModelAdmin):
    inlines = [ProductDetailsInline]

admin.site.register(ProductImageModel)
admin.site.register(FormModel)
admin.site.register(ProductPositionModel)
admin.site.register(TransactionModel)
from django.urls import path
from .views import (
    ProductView,
    ProductImageView,
    FormView,
    pay,
    payment_status,
    payment_succeed,
)


urlpatterns = [
    path('products/', ProductView.as_view() , name="products"),
    path('products/<int:pk>', ProductView.as_view(), name="products-with-pk"),
    path('product-images/', ProductImageView.as_view(), name="product-images"),
    path('product-images/<int:pk>', ProductImageView.as_view(), name="product-images-with-pk"),
    path('forms/', FormView.as_view(), name="forms"),
    path('forms/<int:pk>', FormView.as_view(), name="forms-with-pk"),
    path('pay/', pay, name='pay'),
    path('payment/status/', payment_status, name='payment-status'),
    path('payment/succeed/', payment_succeed, name="payment-succeed")
]
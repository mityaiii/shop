# from datetime import timezone
import uuid
from django.db import models
from typing import Final
from django.core.validators import MinValueValidator
from djmoney.models.fields import MoneyField
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone


MAX_LENGTH: Final[int] = 255 


class ProductImageModel(models.Model):
    title = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name="Название",
    )

    image = models.ImageField(
        upload_to='profile_photos/',
        verbose_name='Фотография',
    )

    class Meta:
        verbose_name_plural = "Фотографии товара"

    def __str__(self) -> str:
        return f"Фотография: {self.title}"


class ProductModel(models.Model):
    title = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name="Название",
    )

    brand = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name="Подзаголовок",
        null=True,
        blank=True,
    )

    description = models.TextField(verbose_name='Описание')

    price = MoneyField(max_digits=14, decimal_places=2, default_currency='RUB')

    weight = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name="Вес",
        validators=[MinValueValidator(0.01)],
    )

    images = models.ManyToManyField(
        ProductImageModel,
        verbose_name="Фотографии товара",
        null=True,
        blank=True,
    )

    quantity = models.PositiveIntegerField(
        verbose_name="Количество"
    )

    class Meta:
        ordering = ["title"]
        verbose_name_plural = "Товары"

    def __str__(self) -> str:
        return f"Товар: {self.title}"


class ProductDetailModel(models.Model):
    description = models.TextField(
        verbose_name="Описание",
    )

    compound = models.TextField(
        verbose_name="Состав",
    )

    expiration_date = models.PositiveSmallIntegerField(
        verbose_name="Срок годности",
    )

    quantity = models.PositiveSmallIntegerField(
        verbose_name="Количество",
    )

    number_of_servings = models.PositiveIntegerField(
        verbose_name="Количество порций",
        null=True,
        blank=True,
    )

    serving_weight = models.PositiveIntegerField(
        verbose_name="Вес порции",
        null=True,
        blank=True,
    )

    product = models.OneToOneField(
        ProductModel,
        verbose_name="Продукт",
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )


class FormModel(models.Model):
    PHONE_NUMBER_LENGTH: Final = 20
 
    name = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name="Имя",
    )

    email = models.EmailField(
        verbose_name="Почта",
    )

    phone_number = models.CharField(
        max_length=PHONE_NUMBER_LENGTH,
        verbose_name="Номер телефона"
    )

    city = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name="Город",
    )

    street = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name="Улица"
    )

    house = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name="Дом",
    )

    comment = models.TextField(
        verbose_name="Комментарий",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name_plural = "Заявки"

    def __str__(self) -> str:
        return f"Товар: {self.email}"


class ProductPositionModel(models.Model):
    product = models.ForeignKey(ProductModel, verbose_name="id продукта", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name="Число")
    form = models.ForeignKey(FormModel, verbose_name="id Корзины", on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "Заявки"

    def __str__(self) -> str:
        return f"Товар: {self.product}"
        

class TransactionModel(models.Model):
    form = models.ForeignKey(to=FormModel, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=50, db_index=True)  # API ID
    payment_url = models.CharField(max_length=120, db_index=True) # API URL
    secret_key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    timestamp = models.DateTimeField(default=timezone.now)
    reverted = models.BooleanField(default=False)

    TRANSACTION_STATUS_CHOICES = [
        ('pending', 'Ожидание оплаты'),
        ('paid', 'Оплачено'),
        ('failed', 'Ошибка оплаты'),
        ('refunded', 'Возврат средств'),
    ]

    transaction_status = models.CharField(
        max_length=10,
        choices=TRANSACTION_STATUS_CHOICES,
        default='pending',
    )

    class Meta:
        verbose_name_plural = "Оплаты"

    def __str__(self):
        return f"Transaction for Payment {self.form} with ID {self.payment_id} ({self.transaction_status})"
    
    @staticmethod
    def reduce_quantity(transaction_id): # TODO: use correct type hint
        try:
            with transaction.atomic():
                my_transaction = get_object_or_404(TransactionModel, transaction_id)
                form = my_transaction.form

                product_positions = ProductPositionModel.objects.filter(form=form)
                for product_position in product_positions:
                    product = ProductModel.objects.select_for_update().get(pk=product_position.product)
                    
                    if product.quantity >= product_position.quantity:
                        product.quantity -= product_position.quantity
                        product.save(update_fields=['quantity'])
                    else:
                        return False
                    
                return True
        except Exception:
            return False


    @staticmethod
    def revert_quantity(transaction_id):
        try:
            with transaction.atomic():
                my_transaction = get_object_or_404(TransactionModel, transaction_id)
                form = my_transaction.form

                product_positions = ProductPositionModel.objects.filter(form=form)
                for product_position in product_positions:
                    product = ProductModel.objects.select_for_update().get(pk=product_position.product)
                    product.quantity += product_position.quantity
                    product.save(update_fields=['quantity'])

                return True    

        except Exception:
            return False

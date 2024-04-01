import uuid
import typing
from yookassa import Payment
from .models import TransactionModel, ProductModel, ProductPositionModel 
from django.core.mail import send_mail

import logging

logger = logging.getLogger(__name__)


def create_payment(product_positions: typing.List[ProductPositionModel], form, credentials):
    transactions = TransactionModel.objects.filter(form=form, transaction_status='pending')
    if transactions.exists():
        return Payment.find_one(transactions.first().payment_id)
    
    amount = 0
    for product_position in product_positions:
        amount += product_position.product.price * product_position.quantity
        if product_position.quantity > product_position.product.quantity:
            raise Exception("less product")

    payment = Payment.create({
        "amount": {
            "value": amount.amount,
            "currency": amount.currency
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "127.0.0.0:8000/api/payment_succeed"
        },
        "capture": True,
        "description": credentials
    }, uuid.uuid4())

    transaction = TransactionModel.objects.get_or_create(
        form=form,
        payment_id=payment.id,
        payment_url=payment.confirmation.confirmation_url,
        transaction_status='pending'
    )[0]

    transaction.save()
    

    return payment


def get_payment_link(payment):
    confirmation_url = payment.confirmation.confirmation_url
    return confirmation_url


def get_payment_id(payment):
    return payment.id


def get_payment_status(payment_id):
    payment = Payment.find_one(payment_id)
    return payment.status


def payment_status_handler(payment_id, payment_status):
    transaction = TransactionModel.objects.get(payment_id=payment_id)

    if payment_status == 'pending':
        transaction.transaction_status = 'pending'
    elif payment_status == 'waiting_for_capture':
        transaction.transaction_status = 'pending'
    elif payment_status == 'succeeded':
        if send_email(transaction.form.email):
            transaction.transaction_status = 'paid'
            TransactionModel.reduce_quantity(transaction)
        else:
            transaction.transaction_status = 'failed'
            TransactionModel.revert_quantity(transaction)
    elif payment_status == 'canceled':
        transaction.transaction_status = 'failed'


    logger.info(f"Transaction {transaction.id} has status {transaction.transaction_status}")
    transaction.save()


def send_email(recipient_mail: str) -> bool:
    try:
        send_mail(
            "Subject here",
            "Here is the message.",
            "example.email@inbox.com",
            [recipient_mail],
            fail_silently=False,
        )

        return True
    except Exception as ex:
        logger.exception("Transction with an error occurred: %s", ex)
        return False
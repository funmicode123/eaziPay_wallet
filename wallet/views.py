import uuid
from decimal import Decimal

import requests
from django.core.mail import send_mail
from django.db import transaction
from django.dispatch import receiver
from rest_framework import status

from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404
import requests

from eaziPay import settings
from wallet.models import Transaction, Wallet
from wallet.serializer import FundSerializer, TransferSerializer


# Create your views here.

@api_view()

def welcome (request):
    return Response(f"Welcome to EaziPay Wallet page")

def greeting(request, name):
    return render(request, 'hello.html', {'name':name})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fund_wallet(request):
    data = FundSerializer(data=request.data)
    data.is_valid(raise_exception=True)
    amount = data.validated_data['amount']
    amount *=100
    email = request.user.email
    reference = f"ref_{uuid.uuid4().hex}"
    Transaction.objects.create(
        reference=reference,
        amount=amount,
        sender=request.user
    )
    url = 'https://api.paystack.co/transaction/initialize'
    secret= settings.PAYSTACK_SECRET_KEY
    headers = {
        "Authorization": f"Bearer {secret}",
    }
    data = {
        'amount': amount,
        'reference': reference,
        'email': email,
        'callback_url': "http://localhost:8000/wallet/fund/verify",
    }
    try:
        response_str = requests.post(url=url, json=data, headers=headers)
        response = response_str.json()
        if response['status']:
            return Response(data=response['data'], status=status.HTTP_200_OK)
    except requests.exceptions.RequestException as e:
        return Response(data={"message":"Unable to preform transaction {e}"}, status=status.HTTP_400_BAD_REQUEST)

@api_view()
def verify_fund(request):
    reference = request.GET.get('reference') or request.GET.get('trxref')
    secret = settings.PAYSTACK_SECRET_KEY
    headers = {
        "Authorization": f"Bearer {secret}",
    }
    url = f'https://api.paystack.co/transaction/verify/{reference}'
    response_str = requests.get(url=url, headers=headers)
    response = response_str.json()
    if response['status'] and response['data']['status'] == "success":
        amount = Decimal(response['data']['amount']) / 100

        try:
            transaction = Transaction.objects.get(reference=reference, verified = False)
        except Transaction.DoesNotExist:
            return Response(data={"message":"Transaction not found"}, status=status.HTTP_404_NOT_FOUND)
        wallet = get_object_or_404(Wallet, user=transaction.sender)
        wallet.deposit(amount)
        transaction.verified = True
        transaction.save()

        subject = "EaziPay Transaction Alert"
        message = f"""
        *****   Deposit Transaction occupied on your wallet   *****
                Amount: {amount}
                from: {transaction.sender.username} 
        *****   Thank you for using EaziPay         *****
        """
        from_email = settings.EMAIL_HOST_USER
        receiver_email =transaction.sender.email
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[receiver_email]
            )
        except Exception as error:
            return Response({"message": f"Email sending failed: {error}"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data={"message":"Deposit successful"}, status=status.HTTP_200_OK)
    return Response(data={"message":"Transaction not successful"}, status=status.HTTP_404_NOT_FOUND)


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def transfer(request):
#     serializer = TransferSerializer(data=request.data)
#     serializer.is_valid(raise_exception=True)
#     data = serializer.validated_data
#
#     amount = int(data['amount'] * 100)
#     account_number = data['account_number']
#     bank_code = data['bank_code']
#     recipient_name = data['recipient_name']
#     reference = f"ref_{uuid.uuid4().hex}"
#
#     sender_wallet = Wallet.objects.get(user=request.user)
#
#     if sender_wallet.balance < Decimal(amount) / 100:
#         return Response({"message": "Insufficient funds"}, status=status.HTTP_400_BAD_REQUEST)
#
#     recipient_url = "https://api.paystack.co/transferrecipient"
#     headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
#     recipient_payload = {
#         "type": "nuban",
#         "name": recipient_name,
#         "account_number": account_number,
#         "bank_code": bank_code,
#         "currency": "NGN",
#         "reference": reference
#     }
#
#     try:
#         recipient_res = requests.post(recipient_url, json=recipient_payload, headers=headers)
#         recipient_data = recipient_res.json()
#         if not recipient_data['status']:
#             return Response({"message": "Recipient creation failed"}, status=status.HTTP_400_BAD_REQUEST)
#
#         recipient_code = recipient_data['data']['recipient_code']
#
#         transfer_url = "https://api.paystack.co/transfer"
#         transfer_payload = {
#             "source": "balance",
#             "amount": amount,
#             "recipient": recipient_code,
#             "reason": f"Transfer from {request.user.email}"
#         }
#
#         transfer_res = requests.post(transfer_url, json=transfer_payload, headers=headers)
#         transfer_data = transfer_res.json()
#
#         if transfer_data['status']:
#             sender_wallet.withdraw(Decimal(amount) / 100)
#             Transaction.objects.create(
#                 reference=transfer_data['data']['reference'],
#                 amount=Decimal(amount) / 100,
#                 sender=request.user,
#                 recipient_account=account_number,
#                 verified=True
#             )
#             return Response({"message": "Transfer successful", "data": transfer_data['data']},
#                             status=status.HTTP_200_OK)
#
#         return Response({"message": "Transfer failed", "data": transfer_data}, status=status.HTTP_400_BAD_REQUEST)
#
#     except requests.exceptions.RequestException as e:
#         return Response({"message": f"Error connecting to Paystack: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transfer(request):
    data = TransferSerializer(data=request.data)
    data.is_valid(raise_exception=True)
    amount = data.validated_data['amount']
    account_number = data.validated_data['account_number']
    sender = request.user
    sender_wallet = get_object_or_404(Wallet, user=sender)
    receiver_wallet = get_object_or_404(Wallet, account_number=account_number)
    receiver = receiver_wallet.user
    if sender == receiver:
        return Response({"message": "You cannot transfer to yourself"}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        reference = f"ref_{uuid.uuid4().hex}"

        try:
            sender_wallet.withdraw(amount)
        except ValueError:
            return Response(data={"message":"Insufficient funds"}, status=status.HTTP_400_BAD_REQUEST)
        Transaction.objects.create(
            amount=amount,
            sender=sender,
            reference=reference,
            transaction_type="T",
            verified=True
        )

        subject = "EaziPay Transaction Alert"
        message = f"""
               *****   Debit transaction occurred on your wallet   *****
                       You transferred  {amount}
                       from: {sender.first_name} {sender.last_name}
               *****   Thank you for using EaziPay         *****
               """
        from_email = settings.EMAIL_HOST_USER
        receiver_email = sender.email
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[receiver_email]
        )

        receiver_wallet.deposit(amount)
        reference = f"ref_{uuid.uuid4().hex}"
        Transaction.objects.create(
            amount=amount,
            receiver=receiver,
            reference=reference,
            transaction_type="D",
            verified=True
        )

        subject = "EaziPay Transaction Alert"
        message = f"""
                       *****   Credit transaction occurred on your wallet   *****
                               You received:  {amount}
                               from: {sender.first_name} {sender.last_name}
                       *****   Thank you for using EaziPay         *****
                       """
        from_email = settings.EMAIL_HOST_USER
        receiver_email = receiver.email
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[receiver_email]
        )
        return Response({"message": "Transfer Successful"}, status=status.HTTP_200_OK)




"""
curl https://api.paystack.co/transferrecipient
-H "Authorization: Bearer YOUR_SECRET_KEY"
-H "Content-Type: application/json"
-X POST
"""


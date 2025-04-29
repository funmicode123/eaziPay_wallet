from decimal import Decimal

from rest_framework import serializers
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer

from wallet.models import Transaction
from .models import Profile

class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        fields = ['first_name', 'last_name', 'username', 'email', 'password', 'phone_number']

class ProfileSerializer(serializers.ModelSerializer):
    bvn = serializers.CharField(max_length=11, min_length=11)

    class Meta:
        model = Profile
        fields = ['user', 'image', 'address', 'bvn', 'nin']


class WalletSerializer(serializers.Serializer):
    balance = serializers.DecimalField(max_digits=20, decimal_places=2, default=0)
    account_number = serializers.CharField(max_length=10)

    def get_balance(self, obj):
        try:
            balance = Decimal(obj.get('balance', '0.00'))
        except:
            balance = Decimal('0.00')

        return f"₦{balance:,.2f}"


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

class TransactionMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['amount', 'transaction_type', 'transaction_date']

        # def get_amount(self, obj):
        #     amount_in_naira = obj.amount / 100
        #     return f"₦ {amount_in_naira:,.2f}"

class DashBoardSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    image = serializers.ImageField()
    wallet = WalletSerializer()
    recent_transactions = TransactionMiniSerializer(many=True)

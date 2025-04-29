from rest_framework import serializers

class FundSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1000, max_value=10000000)

class TransferSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1000, max_value=10000000)
    account_number = serializers.CharField(min_length=10, max_length=10)
    # bank_code = serializers.CharField(min_length=3, max_length=3)
    # recipient_name = serializers.CharField()

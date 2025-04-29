from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from .models import Profile
from .serializers import ProfileSerializer, DashBoardSerializer
from wallet.models import Wallet, Transaction

class ProfileViewSet(ModelViewSet):
    # permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_queryset(self):
        try:
            return Profile.objects.filter(user=self.request.user)
        except Profile.DoesNotExist:
            return Profile.objects.none()


    def get_permissions(self):
        if self.request.method == "DELETE":
            return [IsAdminUser()]
        else:
            return [IsAuthenticated()]

class DashBoardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DashBoardSerializer

    def get(self, request, *args, **kwargs):
        user = request.user
        wallet = Wallet.objects.get(user=user)
        profile = Profile.objects.filter(user=user).first()
        transactions = Transaction.objects.filter(sender=user).order_by('-transaction_date')[:5]

        profile_image_url = request.build_absolute_uri(profile.image.url) if profile and profile.image else None
        dashboard_data = {
            "username": user.username,
            "email": user.email,
            "image": profile_image_url,
            "wallet": {
                "balance": str(wallet.balance),
                "account_number": wallet.account_number
            },
            "recent_transactions": transactions
        }

        serializer = self.get_serializer(dashboard_data)
        return Response(serializer.data)
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Profile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

        subject = "Welcome to EaziPay 🎉"
        message = f"""
                Hello {instance.first_name},
        
                Welcome to EaziPay! We're excited to have you on board.
        
                Start exploring your dashboard and enjoy our services.
        
                Thanks,
                EaziPay Team
                """
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [instance.email]

        try:
            send_mail(subject, message, from_email, recipient_list)
        except Exception as e:
            print(f"Error sending welcome email: {e}")
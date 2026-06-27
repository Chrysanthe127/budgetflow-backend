from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Transaction
from .serializers import TransactionSerializer
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from .models import LoginAttempt
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.exceptions import ValidationError



class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Transaction.objects.none()  # ← ajout important

    def get_queryset(self):
        return self.request.user.transactions.all().order_by('-date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_stats(request):
    transactions = request.user.transactions.all()
    total_revenus = sum(float(t.montant) for t in transactions if t.type == 'revenu')
    total_depenses = sum(float(t.montant) for t in transactions if t.type == 'depense')
    return Response({
        'total_revenus': total_revenus,
        'total_depenses': total_depenses,
        'solde': total_revenus - total_depenses
    })

    
# Inscription (création de compte)
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '')
    if not username or not password:
        return Response({'error': 'Nom utilisateur et mot de passe requis'}, status=400)
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Nom déjà utilisé'}, status=400)
    User.objects.create_user(username=username, email=email, password=password)
    return Response({'message': 'Compte créé'}, status=201)
# Demande de réinitialisation de mot de passe (envoi d'email)
@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email requis'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Pour des raisons de sécurité, on ne révèle pas si l'email existe ou non
        return Response({'message': 'Si un compte existe avec cet email, un lien vous sera envoyé.'}, status=status.HTTP_200_OK)

    # Générer un token et un uid
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    # Construire le lien de réinitialisation (à adapter à votre frontend)
    reset_link = f"http://localhost:8081/reset-password?uid={uid}&token={token}"

    # Envoyer l'email (pour les tests, on affiche dans la console)
    send_mail(
        'Réinitialisation de votre mot de passe',
        f'Cliquez sur ce lien pour réinitialiser votre mot de passe : {reset_link}',
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
    return Response({'message': 'Un email vous a été envoyé.'}, status=status.HTTP_200_OK)

# Confirmation de réinitialisation (nouveau mot de passe)
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_confirm(request):
    uid = request.data.get('uid')
    token = request.data.get('token')
    new_password = request.data.get('new_password')

    if not uid or not token or not new_password:
        return Response({'error': 'Paramètres manquants'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        uid_decoded = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=uid_decoded)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({'error': 'Lien invalide'}, status=status.HTTP_400_BAD_REQUEST)

    if not default_token_generator.check_token(user, token):
        return Response({'error': 'Token invalide ou expiré'}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()
    return Response({'message': 'Mot de passe réinitialisé avec succès'}, status=status.HTTP_200_OK)





        



        
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        # Vérifier si l'utilisateur existe
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # On simule un utilisateur pour ne pas donner d'indice
            raise ValidationError('Nom d’utilisateur ou mot de passe incorrect.')
        
        # Compter les échecs dans la dernière minute
        one_minute_ago = timezone.now() - timedelta(minutes=1)
        failed_attempts = LoginAttempt.objects.filter(
            user=user,
            was_successful=False,
            timestamp__gte=one_minute_ago
        ).count()
        
        if failed_attempts >= 3:
            raise ValidationError('Trop de tentatives. Veuillez attendre 1 minute.')
        
        # Tentative de validation
        try:
            data = super().validate(attrs)
            # Succès
            LoginAttempt.objects.create(user=user, was_successful=True)
            return data
        except Exception as e:
            # Échec
            LoginAttempt.objects.create(user=user, was_successful=False)
            raise ValidationError('Nom d’utilisateur ou mot de passe incorrect.')

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
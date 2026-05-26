from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes

from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response

from menu.models import MenuItem

from .serializers import MenuItemSerializer


# =========================
# PRODUCTS API
# =========================

@api_view(['GET'])

@permission_classes([
    IsAuthenticated
])

def products_api(request):

    products = MenuItem.objects.all()

    serializer = MenuItemSerializer(

        products,

        many=True

    )

    return Response({

        'user': request.user.username,

        'products': serializer.data

    })  
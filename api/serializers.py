from rest_framework import serializers

from menu.models import MenuItem


# =========================
# MENU ITEM SERIALIZER
# =========================

class MenuItemSerializer(

    serializers.ModelSerializer

):

    class Meta:

        model = MenuItem

        fields = '__all__'
from rest_framework import serializers
from .models import MainCategory, SubCategory, MenuItem


class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = [
            'id', 'name', 'description', 'price', 'promo_price',
            'photo', 'is_sold_out', 'is_promo', 'is_available',
            'order', 'created_at', 'updated_at'
        ]


class MenuItemWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = [
            'id', 'sub_category', 'name', 'description', 'price',
            'promo_price', 'photo', 'is_sold_out', 'is_promo',
            'is_available', 'order'
        ]


class SubCategorySerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'order', 'is_available', 'items']

    def get_items(self, obj):
        # only show available items to customers
        request = self.context.get('request')
        items = obj.items.all()
        if request and not (request.user.is_authenticated and hasattr(request.user, 'role')):
            items = items.filter(is_available=True)
        return MenuItemSerializer(items, many=True, context=self.context).data


class SubCategoryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ['id', 'main_category', 'name', 'order', 'is_available']


class MainCategorySerializer(serializers.ModelSerializer):
    sub_categories = serializers.SerializerMethodField()

    class Meta:
        model = MainCategory
        fields = ['id', 'name', 'order', 'is_available', 'sub_categories']

    def get_sub_categories(self, obj):
        request = self.context.get('request')
        sub_cats = obj.sub_categories.all()
        if request and not (request.user.is_authenticated and hasattr(request.user, 'role')):
            sub_cats = sub_cats.filter(is_available=True)
        return SubCategorySerializer(sub_cats, many=True, context=self.context).data


class MainCategoryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainCategory
        fields = ['id', 'name', 'order', 'is_available']
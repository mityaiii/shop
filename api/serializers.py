from rest_framework.serializers import ModelSerializer
from .models import (
    ProductImageModel,
    ProductModel,
    ProductPositionModel,
    FormModel,
    ProductDetailModel
)


class ProductImageSerializer(ModelSerializer):
    class Meta:
        model = ProductImageModel
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        excluded_fields = kwargs.pop('excluded_fields', None)
        super(ProductImageSerializer, self).__init__(*args, **kwargs)

        if excluded_fields:
            for field_name in excluded_fields:
                self.fields.pop(field_name)


class ProductSerializer(ModelSerializer):
    class Meta:
        model = ProductModel
        fields = '__all__'


class ProductDetailSerializer(ModelSerializer):
    class Meta:
        model = ProductDetailModel
        fields = '__all__'


class ProductPositionSerializer(ModelSerializer):
    class Meta:
        model = ProductPositionModel
        fields = ['product', 'quantity']


class FormSerializer(ModelSerializer):
    products = ProductPositionSerializer(many=True, required=False)
    
    class Meta:
        model = FormModel
        fields = ['id', 'name', 'email', 'phone_number', 'city', 'street', 'house', 'comment', 'products']
    
    def get_products(self, instance):
        return instance.productpositionmodel_set.all()
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        products_data = self.get_products(instance)
        serialized_products = ProductPositionSerializer(products_data, many=True).data
        data['products'] = serialized_products
        return data
    
    def create(self, validated_data):
        if 'products' in validated_data:
            products_data = validated_data.pop('products')
            form = FormModel.objects.create(**validated_data)
            
            for product_data in products_data:
                ProductPositionModel.objects.create(form=form, **product_data)

            return form

        return FormModel.objects.create(**validated_data)
    
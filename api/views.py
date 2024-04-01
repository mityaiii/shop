from django.shortcuts import get_object_or_404

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view

from .serializers import (
    ProductSerializer,
    ProductImageSerializer,
    FormSerializer,
    ProductDetailSerializer
)

from .utils import (
    payment_status_handler,
    get_payment_status,
    get_payment_id,
    get_payment_link,
    create_payment
)

from .models import (
    ProductModel,
    ProductImageModel,
    ProductPositionModel,
    FormModel
)

class ProductView(ListCreateAPIView, RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        product_id = self.request.query_params.get('id')
        title = self.request.query_params.get('title')

        if product_id:
            return ProductModel.objects.filter(id=product_id).first()
        
        if title:
            return ProductModel.objects.filter(title=title)

        return ProductModel.objects.all()
    
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            product = get_object_or_404(ProductModel, id=kwargs['pk'])
            serializer = self.get_serializer(product)
            return Response(serializer.data, status=status.HTTP_200_OK) 

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, *args, **kwargs):
        product_id = kwargs.get('pk')
        instance = ProductModel.objects.get(id=product_id)

        serializer = ProductSerializer(instance)

        serializer_data = serializer.data
        serializer_data.update(request.data)

        serializer = ProductSerializer(instance, data=serializer_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"message": "product was deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class ProductImageView(ListCreateAPIView, RetrieveUpdateDestroyAPIView):
    serializer_class = ProductImageSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        product_image_id = self.request.query_params.get('id')
        title = self.request.query_params.get('title')

        if product_image_id:
            return ProductImageModel.objects.filter(id=product_image_id).first()
        
        if title:
            return ProductImageModel.objects.filter(title=title)
        
        return ProductImageModel.objects.all()
    
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            product_image = get_object_or_404(ProductImageModel, id=kwargs['pk'])
            serializer = self.get_serializer(product_image)
            return Response(serializer.data, status=status.HTTP_200_OK) 

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, *args, **kwargs):
        product_image_id = kwargs.get('pk')
        instance = ProductImageModel.objects.get(id=product_image_id)

        excluded_fields  = None
        if not('image' in request.data):
            excluded_fields = ['image']

        serializer = ProductImageSerializer(instance, excluded_fields=excluded_fields, partial=True)

        serializer_data = serializer.data
        serializer_data.update(request.data)

        serializer = ProductImageSerializer(instance, data=serializer_data, excluded_fields=excluded_fields, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"message": "contact was deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class FormView(ListCreateAPIView, RetrieveUpdateDestroyAPIView):
    serializer_class = FormSerializer

    def get_queryset(self):
        form_id = self.request.query_params.get('form_id')

        if form_id:
            return FormModel.objects.filter(id=form_id).first()

        return FormModel.objects.all()
    
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            product = get_object_or_404(FormModel, id=kwargs['pk'])
            serializer = self.get_serializer(product)
            return Response(serializer.data, status=status.HTTP_200_OK) 

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        form_id = request.data.get('form_id')    
        form = get_object_or_404(FormModel, id=form_id)

        product_positions = ProductPositionModel.objects.filter(form=form)

        for product_position in product_positions:
            if product_position.product.quantity < product_position.quantity:
                return Response(data="less product in stock than requested", status=status.HTTP_409_CONFLICT)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, *args, **kwargs):
        form_id = kwargs.get('pk')
        instance = FormModel.objects.get(id=form_id)

        serializer = FormSerializer(instance)

        serializer_data = serializer.data
        serializer_data.update(request.data)

        serializer = FormSerializer(instance, data=serializer_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"message": "form was deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class ProductDetailSerializer(ListCreateAPIView, RetrieveUpdateDestroyAPIView):
    serializer_class = ProductDetailSerializer
    

@api_view(['POST'])
def pay(request, *args, **kwargs):
    form_id = request.data.get('form_id')
    
    form = get_object_or_404(FormModel, id=form_id)

    product_positions = ProductPositionModel.objects.filter(form=form)
    credentials = request.data.get('credentials')

    if credentials is None:
        return Response({
            "error": "no credentials"
        })

    if product_positions is None:
        return Response({
            "error": "no products were selected"
        })

    payment = create_payment(product_positions, form, credentials)

    return Response({
        "payment_link": get_payment_link(payment),
        "payment_id": get_payment_id(payment)
    })


@api_view(['GET'])
def payment_status(request, *args, **kwargs):
    payment_id = request.data.get('payment_id')
    if payment_id is None:
        return Response({
            "error": "no payment_id"
        })

    pay_status = get_payment_status(payment_id)
    payment_status_handler(payment_id, pay_status)

    return Response({
        "status": pay_status
    })


@api_view(['GET'])
def payment_succeed(request, *args, **kwargs):
    return Response()
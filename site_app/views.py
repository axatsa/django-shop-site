from django.db.models import Sum, F
from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import Category, Product, CartItem, Favorite, Order
from .serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    CartItemSerializer,
    CartItemCreateSerializer,
    CartSerializer,
    FavoriteSerializer,
    FavoriteCreateSerializer,
    OrderSerializer,
    UserRegisterSerializer,
    UserSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.select_related('category').all().order_by('-created_at')
    permission_classes = [AllowAny]
    filterset_fields = ['category__slug', 'category__id']
    search_fields = ['title']
    ordering_fields = ['price', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductDetailSerializer


class CartViewSet(viewsets.GenericViewSet,
                  mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  mixins.DestroyModelMixin):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Exclude items already included in orders so the cart reflects only pending items
        return CartItem.objects.filter(user=self.request.user, order__isnull=True).select_related('product')

    def get_serializer_class(self):
        if self.action in ['create', 'add']:
            return CartItemCreateSerializer
        return CartItemSerializer

    def perform_create(self, serializer):
        # If item exists for user+product, increase quantity, else create
        product = serializer.validated_data['product']
        quantity = serializer.validated_data.get('quantity', 1)
        item, created = CartItem.objects.get_or_create(user=self.request.user, product=product,
                                                       defaults={'quantity': quantity})
        if not created:
            item.quantity = F('quantity') + quantity
            item.save()
            item.refresh_from_db()
        return item

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = self.perform_create(serializer)
        output = CartItemSerializer(item)
        headers = self.get_success_headers(output.data)
        return Response(output.data, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):
        items = self.get_queryset()
        serialized = CartItemSerializer(items, many=True)
        total = sum([i.get_total_price() for i in items])
        return Response({'items': serialized.data, 'total_price': total})

    @action(detail=False, methods=['post'], url_path='add')
    def add(self, request):
        return self.create(request)

    @action(detail=False, methods=['delete'], url_path=r'remove/(?P<id>[^/.]+)')
    def remove(self, request, id=None):
        instance = self.get_queryset().filter(pk=id).first()
        if not instance:
            return Response(status=status.HTTP_404_NOT_FOUND)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        items = self.get_queryset()
        total = sum([i.get_total_price() for i in items])
        data = CartSerializer({'items': items, 'total_price': total}).data
        return Response(data)

    @action(detail=False, methods=['post'])
    def clear(self, request):
        self.get_queryset().delete()
        return Response({'detail': 'Cart cleared'}, status=status.HTTP_200_OK)


class FavoriteViewSet(viewsets.GenericViewSet,
                      mixins.ListModelMixin,
                      mixins.CreateModelMixin,
                      mixins.DestroyModelMixin):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related('product')

    def get_serializer_class(self):
        if self.action in ['create', 'add']:
            return FavoriteCreateSerializer
        return FavoriteSerializer

    def perform_create(self, serializer):
        Favorite.objects.get_or_create(user=self.request.user, product=serializer.validated_data['product'])

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        favorite, _ = Favorite.objects.get_or_create(user=request.user, product=serializer.validated_data['product'])
        output = FavoriteSerializer(favorite)
        headers = self.get_success_headers(output.data)
        return Response(output.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['post'], url_path='add')
    def add(self, request):
        return self.create(request)

    @action(detail=False, methods=['delete'], url_path=r'remove/(?P<id>[^/.]+)')
    def remove(self, request, id=None):
        instance = self.get_queryset().filter(pk=id).first()
        if not instance:
            return Response(status=status.HTTP_404_NOT_FOUND)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderViewSet(viewsets.GenericViewSet,
                   mixins.ListModelMixin,
                   mixins.CreateModelMixin):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items__product')

    def get_serializer_class(self):
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        cart_items = CartItem.objects.filter(user=request.user, order__isnull=True)
        if not cart_items.exists():
            return Response({'detail': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
        total = sum([i.get_total_price() for i in cart_items])
        order = Order.objects.create(user=request.user, total_price=total)
        order.items.set(cart_items)
        serializer = self.get_serializer(order)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['post'], url_path='create')
    def create_from_cart(self, request):
        return self.create(request)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response(UserSerializer(request.user).data)

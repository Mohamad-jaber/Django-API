from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Orders, Bottle, OrderStatus
from .serializers import (OrdersSerializer, ChangeOrderStatusSerializer, BottleSerializer, BottleOrderSerializer,
                          ReturnBottlesSerializer)
from .permissions import CanChangeOrderStatusPermission, IsAdminUserCustom
from myapp.models import UserTypes
from django.db.models import Case, When, Value, IntegerField
from django.db.models.functions import Coalesce


class OrdersListCreateAPIView(generics.ListCreateAPIView):
    queryset = Orders.objects.all()
    serializer_class = OrdersSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        customer_id = self.kwargs.get('customer_id')
        if customer_id:
            return queryset.filter(customer_id=customer_id).order_by('-order_date')
        elif self.request.user.type == UserTypes.CUSTOMER:
            return queryset.none()  # Return an empty queryset instead of an empty list
        return queryset.annotate(
            custom_order=Case(
                When(order_status=OrderStatus.PENDING, then=Value(1)),
                When(order_status=OrderStatus.APPROVED, then=Value(2)),
                When(order_status=OrderStatus.DELIVERED, then=Value(3)),
                When(order_status=OrderStatus.CANCELLED, then=Value(4)),
                default=Value(5),
                output_field=IntegerField()
            )
        ).order_by('custom_order', 'order_date')

    def create(self, request, *args, **kwargs):
        response = super(OrdersListCreateAPIView, self).create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            response.data = {'message': 'Order created successfully!'}
        return response


class OrdersDetailAPIView(generics.RetrieveAPIView):
    queryset = Orders.objects.all()
    serializer_class = OrdersSerializer
    permission_classes = [permissions.IsAuthenticated]


class ChangeOrderStatusAPIView(APIView):
    permission_classes = [CanChangeOrderStatusPermission]

    def patch(self, request, *args, **kwargs):
        serializer = ChangeOrderStatusSerializer(data=request.data)
        if serializer.is_valid():
            order = serializer.update_order_status(serializer.validated_data)
            return Response({'message': f"Order {order.id} status updated successfully."},
                            status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BottleListCreateAPIView(generics.ListCreateAPIView):
    queryset = Bottle.objects.all()
    serializer_class = BottleSerializer
    permission_classes = [IsAdminUserCustom]


class BottleOrderView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = BottleOrderSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            if isinstance(result, Orders):
                return Response({'status': 'bottles added to order'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'message': result['status']}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReturnBottlesView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ReturnBottlesSerializer(data=request.data)
        if serializer.is_valid():
            # Execute the update logic from the serializer
            serializer.update(None, serializer.validated_data)
            return Response({'message': 'bottles returned'}, status=status.HTTP_200_OK)
        return Response({'message': 'one or more of bottles is returned'}, status=status.HTTP_400_BAD_REQUEST)

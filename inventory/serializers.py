import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Max

from myapp.models import CustomUser as User, Payment
from rest_framework import serializers
from inventory import models
from inventory.models import Bottle, Orders, BottleOrder, BottleStatus, OrderStatus


class OrdersSerializer(serializers.ModelSerializer):
    order_status = serializers.SerializerMethodField()
    order_address = serializers.SerializerMethodField()
    customer = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    customer_name = serializers.SerializerMethodField()
    customer_phoneNamber = serializers.SerializerMethodField()

    def validate(self, attrs):
        print(attrs)
        super().validate(attrs)
        customer = attrs.get('customer')

        # Check if 'customer' is already a user instance, and extract ID if so
        if isinstance(customer, User):
            customer_id = customer.id
        else:
            try:
                # Assuming customer is the ID directly, or convert from string
                customer_id = int(customer)
            except (ValueError, TypeError):
                raise serializers.ValidationError({"customer": "Invalid customer identifier."})

        # Retrieve the user by ID and check type
        try:
            user = User.objects.get(id=customer_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({"customer": "No such user exists."})

        if user.type != 'C':
            raise serializers.ValidationError({"customer": "User must be of type Customer"})

        return attrs

    class Meta:
        model = models.Orders
        fields = (
            'id', 'order_date', 'order_quantity', 'order_status', 'order_notes', 'customer', 'receiver', 'address',
            'total_price', 'order_address', 'customer_name', 'customer_phoneNamber')
        extra_kwargs = {
            'receiver': {'required': False},
        }
        read_only_fields = ['order_date', 'id']
        write_only_fields = ['address']

    def get_order_address(self, obj):
        return obj.address.title if obj.address else None

    def get_order_status(self, obj):
        return obj.get_order_status_display()

    def get_customer_name(self, obj):
        # return  f"{obj.customer.first_name} {obj.customer.first_name}" if obj.customer else None
        return obj.customer.username if obj.customer else None

    def get_customer_phoneNamber(self, obj):
        return obj.customer.phone_number if obj.customer else None

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['order_status'] = models.OrderStatus.APPROVED

        return super().create(validated_data)


class ChangeOrderStatusSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    new_order_status = serializers.CharField()

    def validate_new_order_status(self, value):
        try:
            value = models.OrderStatus[value.upper()]
        except KeyError:
            raise serializers.ValidationError(f"{value} is not a valid choice for new_order_status.")
        return value

    def validate(self, data):
        order_id = data.get('order_id')
        try:
            order = Orders.objects.get(pk=order_id)
        except Orders.DoesNotExist:
            raise serializers.ValidationError("Order does not exist.")
        data['order'] = order
        return data

    def update_order_status(self, validated_data):
        order_id = validated_data.get('order_id')
        new_order_status = validated_data.get('new_order_status')

        order = models.Orders.objects.get(pk=order_id)
        order.order_status = new_order_status
        order.save()
        if new_order_status == OrderStatus.DELIVERED:
            self.create_payment_record(order)

        return order

    def create_payment_record(self, order):
        if not order.customer:
            # Log an error or handle the case where the customer does not exist
            raise serializers.ValidationError("The order's customer does not exist.")
        else:
            # Assuming you have a method or a property `get_special_price` in your customer model
            special_price = order.customer.get_special_price() if hasattr(order.customer, 'get_special_price') else 20

            amount = order.order_quantity * special_price

            # Create the payment record, assuming all foreign keys are valid
            try:
                Payment.objects.create(
                    amount=-amount,
                    customer=order.customer,
                    receiver=None  # Assuming receiver can be None
                )
            except Exception as e:
                # Handle the exception appropriately
                raise serializers.ValidationError(f"Failed to create payment record: {str(e)}")


class BottleSerializer(serializers.ModelSerializer):
    qr_code = serializers.SerializerMethodField()
    bottle_status = serializers.SerializerMethodField()

    class Meta:
        model = Bottle
        fields = ['bottleId', 'number_of_times_Sold', 'bottle_status', 'qr_code']

    def get_bottle_status(self, obj):
        return obj.get_bottle_status_display()

    def get_qr_code(self, obj):
        if obj.qr_code:
            return obj.qr_code  # Since qr_code is already a data URL, just return it directly
        else:
            qr_code_data = obj.generate_qr_code(obj.bottleId)
            obj.qr_code = qr_code_data  # Save the QR code data URL to the model
            obj.save()
            return qr_code_data


class BottleOrderSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    bottle_ids = serializers.ListField(
        child=serializers.IntegerField()
    )

    def create(self, validated_data):
        order_id = validated_data.get('order_id')
        bottle_ids = validated_data.get('bottle_ids')
        order = Orders.objects.get(pk=order_id)

        bottle_count = BottleOrder.objects.filter(order=order).count()
        if bottle_count == order.order_quantity:
            return {'status': f'cant add more bottles to this order'}

        with transaction.atomic():

            for bottle_id in bottle_ids:
                try:
                    bottle = Bottle.objects.select_for_update().get(pk=bottle_id)
                    if bottle.bottle_status == BottleStatus.SOLD:
                        # Bottle is already sold, return a message
                        return {'status': f'bottle {bottle_id} is sold '}
                    elif bottle.bottle_status == BottleStatus.DISCARDED:
                        # Bottle is discarded, return a message
                        return {'status': f'bottle {bottle_id} is discarded '}
                    else:
                        bottle.bottle_status = BottleStatus.SOLD
                        bottle.save()
                        BottleOrder.objects.create(order=order, bottle=bottle, dateOfReturning=None)
                except ObjectDoesNotExist:
                    # Bottle does not exist, return a message
                    return {'status': f'bottle {bottle_id} does not exist'}

            bottle_count = BottleOrder.objects.filter(order=order).count()
            if bottle_count == order.order_quantity:
                order.order_status = OrderStatus.DELIVERED
                order.save()

            return order


class ReturnBottlesSerializer(serializers.Serializer):
    bottle_ids = serializers.ListField(child=serializers.IntegerField())

    def validate(self, data):
        bottle_ids = data['bottle_ids']
        bottles_with_orders = BottleOrder.objects.filter(
            bottle_id__in=bottle_ids,
            dateOfReturning__isnull=True  # Filter for orders that have not been returned
        ).annotate(
            latest_order_id=Max('order__id')
        )

        bottle_ids_with_valid_orders = {bo.bottle_id for bo in bottles_with_orders}
        if len(bottle_ids_with_valid_orders) != len(bottle_ids):
            raise serializers.ValidationError("One or more bottles do not have unreturned orders or are invalid.")

        return data

    def update(self, instance, validated_data):
        bottle_ids = validated_data.get('bottle_ids')
        # Process the return based on the last order associated without a return date
        bottles_with_orders = BottleOrder.objects.filter(
            bottle_id__in=bottle_ids,
            dateOfReturning__isnull=True
        ).annotate(
            latest_order_id=Max('order__id')
        )

        with transaction.atomic():
            for bottle_order in bottles_with_orders:
                bottle = bottle_order.bottle
                order = Orders.objects.get(id=bottle_order.latest_order_id)

                bottle.number_of_times_Sold += 1
                if bottle.number_of_times_Sold >= 35:
                    bottle.bottle_status = BottleStatus.DISCARDED
                else:
                    bottle.bottle_status = BottleStatus.AVAILABLE
                bottle.save()

                # Update the BottleOrder instance to mark it as returned
                bottle_order.dateOfReturning = datetime.date.today()
                bottle_order.save()

        return instance

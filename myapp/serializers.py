from decimal import Decimal

from django.contrib.auth import authenticate
from django.db.models import Sum, Q
from rest_framework import serializers
from .models import CustomUser as User, Payment
from .models import Address, UserTypes


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ["id", "title", "user"]
        extra_kwargs = {
            'user': {'required': False}
        }

    def create(self, validated_data):
        user_instance = validated_data.pop('user', None)

        if user_instance is None:
            raise serializers.ValidationError("User ID is required.")

        user_id = user_instance.id  # Get the primary key (id) from the user instance
        user = User.objects.get(pk=user_id)
        if user.type != "C":
            raise serializers.ValidationError("Type of user is not Customer")
        address = Address.objects.create(user=user, **validated_data)
        return address


class UserSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True, required=False)
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})
    service_type = serializers.SerializerMethodField()
    type = serializers.ChoiceField(choices=UserTypes.choices, write_only=True)
    wallet_balance = serializers.SerializerMethodField(read_only=True)
    last_order_date = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'email', 'first_name', 'last_name', 'type', 'addresses', 'service_type',
                  'wallet_balance', 'phone_number', 'specialBottlePrice', 'last_order_date')
        extra_kwargs = {'specialBottlePrice': {'required': False}}

    def get_last_order_date(self, obj):
        # Filter orders by this user, order by date descending
        last_order = obj.customer.order_by('-order_date').first()
        if last_order:
            return last_order.order_date
        return None

    def get_service_type(self, obj):
        # Custom method to display the user type using get_<field>_display()
        return obj.get_type_display()

    def get_wallet_balance(self, obj):
        if obj.type != 'C':
            return 0

        balance = obj.payments_as_customer.aggregate(
            total_balance=Sum('amount')
        )['total_balance'] or Decimal('0.00')

        return balance

    def validate(self, attrs):
        super().validate(attrs)
        # Password validation when creating a new user
        password = attrs.get('password')
        if not self.instance and not password:
            raise serializers.ValidationError("Password is required for new users.")
        return attrs

    def create(self, validated_data):
        addresses_data = validated_data.pop('addresses', [])
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            type=validated_data['type'],
            phone_number=validated_data['phone_number'],
            specialBottlePrice=validated_data.get('specialBottlePrice')
        )
        user.set_password(validated_data['password'])
        user.save()

        # Assuming type 'C' stands for Customer and they can have addresses
        if user.type == 'C':
            for address_data in addresses_data:
                Address.objects.create(user=user, **address_data)

        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        print(username, password)

        if username and password:
            user = authenticate(username=username, password=password)

            if user:
                attrs['user'] = user
                return attrs
            else:
                raise serializers.ValidationError("Unable to log in with provided credentials.")
        else:
            raise serializers.ValidationError("Both username and password are required.")


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(style={'input_type': 'password'})
    new_password = serializers.CharField(style={'input_type': 'password'})
    confirm_new_password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        new_password = attrs.get('new_password')
        confirm_new_password = attrs.get('confirm_new_password')

        if new_password != confirm_new_password:
            raise serializers.ValidationError("New passwords must match.")

        return attrs


class PaymentSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    customer_name = serializers.SerializerMethodField()
    receiver_name = serializers.SerializerMethodField()

    def get_customer_name(self, obj):
        # return  f"{obj.customer.first_name} {obj.customer.first_name}" if obj.customer else None
        return obj.customer.username if obj.customer else None

    def get_receiver_name(self, obj):
        return obj.receiver.username if obj.receiver else None

    class Meta:
        model = Payment
        fields = ['id', 'amount', 'customer', 'receiver', 'created_at', 'customer_name', 'receiver_name']
        read_only_fields = ['receiver', 'created_at']

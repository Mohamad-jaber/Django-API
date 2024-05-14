from rest_framework.exceptions import ValidationError
from .models import CustomUser as User, Payment, UserTypes
from rest_framework import generics, status, permissions, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Address
from .permissions import IsNotCustomer
from .serializers import UserSerializer, AddressSerializer, PaymentSerializer, LoginSerializer, ChangePasswordSerializer
from rest_framework_simplejwt.tokens import RefreshToken


class UserListCreate(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsNotCustomer]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response({'message': 'Success', 'data': serializer.data}, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response({'message': 'Added Successfully'}, status=status.HTTP_201_CREATED, headers=headers)
        except ValidationError as e:
            # Extract the first error and include the field name
            if e.detail:
                # Get the first key in the error dictionary and its first associated message
                field, errors = next(iter(e.detail.items()))
                first_error = errors[0]
                error_message = f"{field}: {first_error}"
            else:
                # Generic message if detail is empty (unlikely but safer to handle)
                error_message = "Invalid input."
            return Response({'message': error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Generic exception handling
            return Response({'message': 'An error occurred', 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CustomersListCreate(generics.ListAPIView):
    queryset = User.objects.all().filter(type=UserTypes.CUSTOMER)
    serializer_class = UserSerializer
    permission_classes = [IsNotCustomer]


class EmployeesListCreate(generics.ListAPIView):
    queryset = User.objects.all().exclude(type=UserTypes.CUSTOMER)
    serializer_class = UserSerializer
    permission_classes = [IsNotCustomer]


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            user_data = UserSerializer(user).data

            user_data['wallet_balance'] = str(user_data['wallet_balance'])

            # Add custom data to the token payload
            refresh['userId'] = user_data['id']
            refresh['userName'] = user_data['username']
            refresh['fullName'] = f"{user_data['first_name']} {user_data['last_name']}"
            refresh['email'] = user_data['email']
            refresh['role'] = user_data['service_type']
            refresh['phoneNumber'] = user_data['phone_number']
            refresh['wallet'] = user_data['wallet_balance']

            return Response({
                'userId': user_data['id'],
                'userName': user_data['username'],
                'fullName': f"{user_data['first_name']} {user_data['last_name']}",
                'email': user_data['email'],
                'role': user_data['service_type'],
                'phoneNumber': user_data['phone_number'],
                'token': str(refresh.access_token),
                'wallet': user_data['wallet_balance']
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserEdit(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        user = self.request.user
        requested_pk = self.kwargs.get('pk')
        print(user.pk)
        if user.type == UserTypes.Admin:
            return User.objects.filter(pk=requested_pk)
        elif user.pk == requested_pk:
            return User.objects.filter(pk=requested_pk)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            data = serializer.validated_data
            old_password = data.get('old_password')
            new_password = data.get('new_password')

            if not user.check_password(old_password):
                return Response({'error': 'Wrong old password.'}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.save()

            return Response({'success': 'Password updated successfully.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddressListCreate(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Address.objects.all()
    serializer_class = AddressSerializer


class AddressEdit(generics.RetrieveUpdateAPIView):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = []
    authentication_classes = []
    lookup_field = "pk"


class PaymentListCreateAPIView(generics.ListCreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def get_queryset(self):
        user = self.request.user
        if user.type == 'C':
            return Payment.objects.filter(customer=user).order_by('-created_at')
        else:
            return Payment.objects.all().order_by('-created_at')

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), IsNotCustomer()]
        else:
            return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        if self.request.user.type == 'C':
            raise serializers.ValidationError({'error': 'Customers cannot create payments'})
        else:
            serializer.save(receiver=self.request.user)

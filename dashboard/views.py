from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Avg, Count
from django.db.models.functions import TruncDay, TruncMonth
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView
from inventory.models import *
from myapp.models import *


# Create your views here.
class IndexView(UserPassesTestMixin, TemplateView):
    template_name = "dashboard/index.html"
    login_url = reverse_lazy('admin:login')

    def test_func(self):
        return self.request.user.is_authenticated

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Calculate the total number of orders
        total_orders = Orders.objects.count()

        # Calculate the total number of bottles across all orders
        total_bottles = BottleOrder.objects.count()

        # Calculate average bottles per order if there are any orders
        if total_orders > 0:
            avg_bottles_per_order = total_bottles / total_orders
        else:
            avg_bottles_per_order = 0

        context['total_orders'] = total_orders
        context['avg_bottles_per_order'] = avg_bottles_per_order.__ceil__()

        total_payment = Payment.objects.count()

        context['total_payment'] = total_payment

        # Calculate average payment per day
        payments_per_day = Payment.objects.annotate(day=TruncDay('created_at')).values('day').annotate(
            avg_daily=Avg('amount')).order_by('day')

        # for x in payments_per_day:
        #     print(x)

        if payments_per_day:
            total_avg_per_day = sum(item['avg_daily'] for item in payments_per_day) / len(payments_per_day)
        else:
            total_avg_per_day = 0

        # Calculate average payment per month
        payments_per_month = Payment.objects.annotate(month=TruncMonth('created_at')).values('month').annotate(
            avg_monthly=Avg('amount')).order_by('month')
        if payments_per_month:
            total_avg_per_month = sum(item['avg_monthly'] for item in payments_per_month) / len(payments_per_month)
        else:
            total_avg_per_month = 0

        context['avg_payment_per_day'] = total_avg_per_day
        context['avg_payment_per_month'] = total_avg_per_month

        # Calculate the total number of bottles
        total_bottles = Bottle.objects.count()

        # Calculate bottles by status
        bottles_by_status = Bottle.objects.values('bottle_status').annotate(count=Count('bottle_status'))
        # print(bottles_by_status)
        status_dict = {status['bottle_status']: status['count'] for status in bottles_by_status}
        # print(status_dict)

        # Assigning counts to context
        context['total_bottles'] = total_bottles
        context['available_bottles'] = status_dict.get(BottleStatus.AVAILABLE, 0)
        context['sold_bottles'] = status_dict.get(BottleStatus.SOLD, 0)
        context['discarded_bottles'] = status_dict.get(BottleStatus.DISCARDED, 0)

        # Get the top five customers with the highest number of orders
        top_customers = Orders.objects.values('customer__username').annotate(
            order_count=Count('id')
        ).order_by('-order_count')[:5]

        context['top_customers'] = top_customers

        return context


class PaymentListView(UserPassesTestMixin , ListView):
    model = Payment
    template_name = 'dashboard/payment.html'
    context_object_name = 'payments'

    login_url = reverse_lazy('admin:login')

    def test_func(self):
        return self.request.user.is_authenticated

    def get_queryset(self):
        return Payment.objects.all().order_by('-created_at')


class OrderListView(UserPassesTestMixin ,ListView):
    model = Orders
    template_name = 'dashboard/orders.html'
    context_object_name = 'orders'

    login_url = reverse_lazy('admin:login')

    def test_func(self):
        return self.request.user.is_authenticated

    def get_queryset(self):
        return Orders.objects.all().order_by('-order_date')


class BottlesListView(UserPassesTestMixin,ListView):
    model = Bottle
    template_name = 'dashboard/bottles.html'
    context_object_name = 'bottles'
    login_url = reverse_lazy('admin:login')

    def test_func(self):
        return self.request.user.is_authenticated


    def get_queryset(self):
        return Bottle.objects.all()
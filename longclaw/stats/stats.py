"""
Various stats/analysis calculations
"""
import itertools
import calendar
from datetime import datetime
from django.db.models import Q, Sum, F
from longclaw.orders.models import Order, OrderItem
from wagtail.core.permission_policies.collections \
    import CollectionPermissionPolicy


def current_month():
    now = datetime.now()
    n_days = calendar.monthrange(now.year, now.month)[1]
    month_start = datetime.strptime('{}{}{}'.format(now.year, now.month, 1), '%Y%m%d')
    month_end = datetime.strptime('{}{}{}'.format(now.year,now.month, n_days), '%Y%m%d')
    return month_start, month_end


def sales_for_time_period(from_date, to_date, user):
    """
    Get all sales for a given time period
    """
    sales = Order.objects.filter(
        Q(payment_date__lte=to_date) & Q(payment_date__gte=from_date)
    ).exclude(status=Order.CANCELLED)

    if user.is_active and user.is_authenticated and not user.is_superuser:

        perm_policy = CollectionPermissionPolicy(
            Order, auth_model=Order
        )

        collections = perm_policy._collections_with_perm(
            user, ['add', 'change', 'delete']
        )

        sales = sales.filter(collection__in=collections)

    return sales


def daily_sales(from_date, to_date, user):
    sales = sales_for_time_period(from_date, to_date, user)
    grouped = itertools.groupby(sales, lambda order: order.payment_date.strftime("%Y-%m-%d"))
    return grouped


def sales_by_product(from_date, to_date, user):
    order_objects = sales_for_time_period(from_date, to_date, user)

    sales = OrderItem.objects.filter(
        Q(order__in=order_objects)
    ).exclude(
        order__status=Order.CANCELLED
    ).annotate(
        title=F('product__product__title')
    ).values(
        'title'
    ).annotate(
        quantity=Sum('quantity')
    ).order_by('-quantity')

    return sales

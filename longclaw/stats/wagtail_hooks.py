import datetime
from wagtail.core import hooks
from wagtail.admin.site_summary import SummaryItem
from longclaw.orders.models import Order
from longclaw.products.models import ProductWithCollectionBase
from longclaw.stats import stats
from longclaw.configuration.models import Configuration
from longclaw.utils import ProductVariant, maybe_get_product_model
from wagtail.core.permission_policies.collections \
    import CollectionPermissionPolicy



class LongclawSummaryItem(SummaryItem):
    order = 10
    template = 'stats/summary_item.html'

    def get_context(self):
        return {
            'total': 0,
            'text': '',
            'url': '',
            'icon': 'icon-doc-empty-inverse'
        }

class OutstandingOrders(LongclawSummaryItem):
    order = 10
    def get_context(self):
        user = self.request.user

        orders = Order.objects.all()

        if user.is_active and user.is_authenticated and not user.is_superuser:

            permission_policy = CollectionPermissionPolicy(
                Order, auth_model=Order
            )

            collections = permission_policy._collections_with_perm(
                user, ['add', 'change', 'delete']
            )

            orders = Order.objects.filter(collection__in=collections)

        orders = orders.filter(status=Order.SUBMITTED)

        return {
            'total': orders.count(),
            'text': 'Outstanding Orders',
            'url': '/admin/orders/order/',
            'icon': 'icon-warning'
        }


class ProductCount(LongclawSummaryItem):
    order = 20

    def get_context(self):
        product_model = maybe_get_product_model()
        if product_model:
            all_products = product_model.objects.all()
            count = all_products.count()
            if count > 0:
                some_product = all_products[0]
                if isinstance(some_product, ProductWithCollectionBase):
                    user = self.request.user
                    if user.is_active and user.is_authenticated and not user.is_superuser:
                        permission_policy = CollectionPermissionPolicy(
                            product_model, auth_model=product_model
                        )

                        collections = permission_policy._collections_with_perm(
                            user, ['add', 'change', 'delete']
                        )

                        all_products = all_products.filter(collection__in=collections)
                        count = all_products.count()

        else:
            count = ProductVariant.objects.all().count()

        return {
            'total': count,
            'text': 'Product',
            'url': '',
            'icon': 'icon-list-ul'
        }

class MonthlySales(LongclawSummaryItem):
    order = 30
    def get_context(self):
        settings = Configuration.for_site(self.request.site)
        month_start, month_end = stats.current_month()
        sales = stats.sales_for_time_period(
            month_start, month_end, self.request.user
        )

        return {
            'total': "{}{}".format(settings.currency_html_code,
                                   sum(order.total for order in sales)),
            'text': 'In sales this month',
            'url': '/admin/orders/order/',
            'icon': 'icon-tick'
        }

class LongclawStatsPanel(SummaryItem):
    order = 110
    template = 'stats/stats_panel.html'
    def get_context(self):
        month_start, month_end = stats.current_month()
        daily_sales = stats.daily_sales(
            month_start, month_end, self.request.user
        )
        labels = [(month_start + datetime.timedelta(days=x)).strftime('%Y-%m-%d')
                  for x in range(0, datetime.datetime.now().day)]
        daily_income = [0] * len(labels)
        for k, order_group in daily_sales:
            i = labels.index(k)
            daily_income[i] = float(sum(order.total for order in order_group))

        popular_products = stats.sales_by_product(
            month_start, month_end, user=self.request.user
        )[:5]

        return {
            "daily_income": daily_income,
            "labels": labels,
            "product_labels": list(popular_products.values_list('title', flat=True)),
            "sales_volume": list(popular_products.values_list('quantity', flat=True))
        }




@hooks.register('construct_homepage_summary_items')
def add_longclaw_summary_items(request, items):

    # We are going to replace everything with our own items
    items[:] = []
    items.extend([
        OutstandingOrders(request),
        ProductCount(request),
        MonthlySales(request)
    ])

@hooks.register('construct_homepage_panels')
def add_stats_panel(request, panels):
    return panels.append(LongclawStatsPanel(request))

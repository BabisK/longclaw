from wagtail.contrib.modeladmin.options import (
    ModelAdmin, modeladmin_register
)
from longclaw.shipping.models import ShippingRate
from django.contrib.admin.utils import quote
from django.utils.translation import ugettext as _
from django.conf.urls import url
from wagtail.contrib.modeladmin.helpers import ButtonHelper
from wagtail.contrib.modeladmin.views import InspectView, IndexView
from wagtail.core.models import Collection
from wagtail.core import hooks
from .forms import GroupShippingRatePermissionFormSet
from longclaw.settings import API_URL_PREFIX
from longclaw.shipping.permissions import permission_policy
from wagtail.admin.menu import MenuItem


# class OrdersMenuItem(MenuItem):
#     def is_shown(self, request):
#         return permission_policy.user_has_any_permission(
#             request.user, ['add', 'change', 'delete']
#         )


class IndexView(IndexView):
    collections = Collection.objects.all()

    def get_queryset(self, request=None):
        if 'collection_id' in self.params and self.params.get('collection_id') == '':
            del self.params['collection_id']
        return super().get_queryset(request)

    def get_context_data(self, **kwargs):
        context = {
            'collections': self.collections
        }
        if 'collection_id' in self.params:
            current_collection = Collection.objects.get(id=self.params.get('collection_id'))
            context.update({'current_collection': current_collection})

        context.update(kwargs)
        return super().get_context_data(**context)

class ShippingRateModelAdmin(ModelAdmin):
    model = ShippingRate
    menu_label = 'Shipping'
    menu_order = 200
    menu_icon = 'site'
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('name', 'rate', 'carrier', 'description', 'collection')
    index_view_class = IndexView
    index_template_name = 'shipping/index.html'


@hooks.register('register_group_permission_panel')
def register_shipping_rate_permissions_panel():
    return GroupShippingRatePermissionFormSet

modeladmin_register(ShippingRateModelAdmin)

from collectionmodeladmin.base import CollectionModelAdmin, collection_modeladmin_register
from longclaw.shipping.models import ShippingRate
from django.contrib.auth.models import Permission


class ShippingRateModelAdmin(CollectionModelAdmin):
    model = ShippingRate
    menu_label = 'Shipping'
    menu_order = 200
    menu_icon = 'site'
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('name', 'rate', 'carrier', 'description', 'collection')
    inspect_view_enabled = False
    index_template_name = 'shipping/index.html'

    def get_queryset(self, request):
        user = request.user
        if user.is_active and user.is_authenticated and user.is_superuser:
            qs = self.model._default_manager.all()
        else:
            perm_policy = self.permission_helper.permission_policy
            collections = perm_policy._collections_with_perm(
                user, ['add', 'change', 'delete']
            )
            qs = self.model._default_manager.filter(collection__in=collections)
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)

        return qs

    def get_permissions_for_registration(self):
        return Permission.objects.none()


collection_modeladmin_register(ShippingRateModelAdmin)

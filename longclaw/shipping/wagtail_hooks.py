from wagtail.contrib.modeladmin.options import (
    ModelAdmin, modeladmin_register
)
from longclaw.shipping.models import ShippingRate
from longclaw.utils import CustomCollectionPermissionHelper
from wagtail.contrib.modeladmin.views import IndexView, CreateView, EditView
from wagtail.core.models import Collection
from wagtail.core import hooks
from .forms import GroupShippingRatePermissionFormSet
from django.contrib.auth.models import Permission


class CreateView(CreateView):

    def get_form_class(self):
        form_class = super().get_form_class()
        user = self.request.user

        if user.is_active and user.is_authenticated and not user.is_superuser:
            perm_policy = self.permission_helper.permission_policy
            collections = perm_policy._collections_with_perm(
                user, ['add', 'change', 'delete']
            )
            form_class.base_fields['collection'].queryset = collections
            form_class.base_fields['collection'].choices.queryset = collections

        return form_class


class EditView(EditView):

    def get_form_class(self):
        form_class = super().get_form_class()
        user = self.request.user

        if user.is_active and user.is_authenticated and not user.is_superuser:
            perm_policy = self.permission_helper.permission_policy
            collections = perm_policy._collections_with_perm(
                user, ['add', 'change', 'delete']
            )
            form_class.base_fields['collection'].queryset = collections
            form_class.base_fields['collection'].choices.queryset = collections

        return form_class


class IndexView(IndexView):

    def get_queryset(self, request=None):
        if 'collection_id' in self.params:
            if self.params.get('collection_id') == '':
                del self.params['collection_id']

        return super().get_queryset(request)

    def get_context_data(self, **kwargs):
        user = self.request.user

        if user.is_active and user.is_authenticated and user.is_superuser:
            self.collections = Collection.objects.all()
        else:
            perm_policy = self.permission_helper.permission_policy
            self.collections = perm_policy._collections_with_perm(
                user, ['add', 'change', 'delete']
            )

        context = {
            'collections': self.collections
        }
        if 'collection_id' in self.params:
            current_collection = Collection.objects.get(
                id=self.params.get('collection_id')
            )
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
    create_view_class = CreateView
    edit_view_class = EditView
    inspect_view_enabled = False
    index_template_name = 'shipping/index.html'
    permission_helper_class = CustomCollectionPermissionHelper

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


@hooks.register('register_group_permission_panel')
def register_shipping_rate_permissions_panel():
    return GroupShippingRatePermissionFormSet


modeladmin_register(ShippingRateModelAdmin)

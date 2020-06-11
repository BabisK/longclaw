from django.conf.urls import url
from django.contrib.admin.utils import quote
from django.contrib.auth.models import Permission
from django.utils.translation import ugettext as _

from wagtail.contrib.modeladmin.options import (
    ModelAdmin, modeladmin_register
)
from wagtail.contrib.modeladmin.helpers import ButtonHelper
from wagtail.contrib.modeladmin.views import \
    InspectView, IndexView, CreateView, EditView
from wagtail.core.models import Collection
from .forms import GroupOrderPermissionFormSet
from wagtail.core import hooks
from longclaw.orders.models import Order
from longclaw.settings import API_URL_PREFIX
from longclaw.utils import CustomCollectionPermissionHelper


class OrderButtonHelper(ButtonHelper):

    detail_button_classnames = []
    cancel_button_classnames = ['no']

    def cancel_button(self, pk, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = ['cancel-button']
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.cancel_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': '',
            'label': _('Cancel'),
            'classname': cn,
            'title': _('Cancel this %s') % self.verbose_name,
        }

    def detail_button(self, pk, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = ['detail-button']
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.detail_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.url_helper.get_action_url('detail', quote(pk)),
            'label': _('View'),
            'classname': cn,
            'title': _('View this %s') % self.verbose_name,
        }

    def get_buttons_for_obj(self, obj, exclude=None, classnames_add=None,
                            classnames_exclude=None):
        if exclude is None:
            exclude = []
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []

        ph = self.permission_helper
        usr = self.request.user
        pk = quote(getattr(obj, self.opts.pk.attname))

        btns = []
        if ph.user_can_inspect_obj(usr, obj):
            btns.append(self.detail_button(
                pk, classnames_add, classnames_exclude))
            btns.append(self.cancel_button(
                pk, classnames_add, classnames_exclude))

        return btns


class DetailView(InspectView):

    def get_page_title(self, **kwargs):
        return "Order #{}".format(self.instance.id)

    def get_page_subtitle(self, **kwargs):
        return ''

    def get_context_data(self, **kwargs):
        context = {
            'order_id': self.instance.id,
            'api_url_prefix': API_URL_PREFIX
        }
        context.update(kwargs)
        new_context = super(DetailView, self).get_context_data(**context)
        return new_context

    def get_template_names(self):
        return 'orders_detail.html'


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


class OrderModelAdmin(ModelAdmin):
    model = Order
    menu_order = 100
    menu_icon = 'list-ul'
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('id', 'status', 'status_note', 'email',
                    'payment_date', 'total_items', 'total')
    list_filter = ('status', 'payment_date', 'email')
    index_view_class = IndexView
    create_view_class = CreateView
    edit_view_class = EditView
    index_template_name = 'orders/index.html'
    inspect_view_enabled = True
    detail_view_class = DetailView
    button_helper_class = OrderButtonHelper
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

    def detail_view(self, request, instance_pk):
        """
        Instantiates a class-based view to provide 'inspect' functionality for
        the assigned model. The view class used can be overridden by changing
        the 'inspect_view_class' attribute.
        """
        kwargs = {'model_admin': self, 'instance_pk': instance_pk}
        view_class = self.detail_view_class
        return view_class.as_view(**kwargs)(request)

    def get_admin_urls_for_registration(self):
        """
        Utilised by Wagtail's 'register_admin_urls' hook to register urls for
        our the views that class offers.
        """
        urls = super(OrderModelAdmin, self).get_admin_urls_for_registration()
        urls = urls + (
            url(self.url_helper.get_action_url_pattern('detail'),
                self.detail_view,
                name=self.url_helper.get_action_url_name('detail')),
        )
        return urls

    def get_permissions_for_registration(self):
        return Permission.objects.none()


modeladmin_register(OrderModelAdmin)


@hooks.register('register_group_permission_panel')
def register_order_permissions_panel():
    return GroupOrderPermissionFormSet

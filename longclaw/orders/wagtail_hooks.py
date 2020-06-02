from django.conf.urls import include, url
from django.urls import reverse
from django.contrib.admin.utils import quote
from django.contrib.auth.models import Permission
from django.utils.translation import ugettext as _
from django.conf.urls import url
from django.urls import reverse

from wagtail.contrib.modeladmin.options import (
    ModelAdmin, modeladmin_register
)
from wagtail.contrib.modeladmin.helpers import ButtonHelper
from wagtail.contrib.modeladmin.views import InspectView, IndexView, CreateView, EditView
from wagtail.core.models import Collection
from .forms import GroupOrderPermissionFormSet
from wagtail.core import hooks
from wagtail.admin.menu import MenuItem
from longclaw.orders.models import Order
from longclaw.settings import API_URL_PREFIX
from longclaw.orders import admin_urls
from longclaw.orders.permissions import OrderPermissionHelper
from wagtail.admin.edit_handlers import ObjectList, FieldPanel
from django.forms.models import fields_for_model, ModelChoiceField
from wagtail.admin.forms.models import (  # NOQA
    DIRECT_FORM_FIELD_OVERRIDES, FORM_FIELD_OVERRIDES, WagtailAdminModelForm, formfield_for_dbfield)


def extract_panel_definitions_from_model_class(model, exclude=None, collections=None):
    if hasattr(model, 'panels'):
        return model.panels

    panels = []

    _exclude = []
    if exclude:
        _exclude.extend(exclude)

    fields = fields_for_model(
        model, exclude=_exclude, formfield_callback=formfield_for_dbfield
    )

    for field_name, field in fields.items():
        if field_name == 'collection' and collections is not None:
            print(str(field))
            print('Valid collections are: ' + str(collections))
            field = ModelChoiceField(queryset = collections)
            print(str(field._get_queryset()))
        try:
            panel_class = field.widget.get_panel()

        except AttributeError:
            panel_class = FieldPanel

        panel = panel_class(field_name)
        panels.append(panel)

    return panels


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
        print('Get buttons for obj....')
        if exclude is None:
            exclude = []
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []

        ph = self.permission_helper
        usr = self.request.user
        pk = quote(getattr(obj, self.opts.pk.attname))

        print('Permission helper is: ' + str(ph))

        btns = []
        if ph.user_can_inspect_obj(usr, obj):
            print('user can inspect Order object...')
            btns.append(self.detail_button(
                pk, classnames_add, classnames_exclude))
            print('Append 1')
            btns.append(self.cancel_button(
                pk, classnames_add, classnames_exclude))
            print('Append 2')
        else:
            print('We failed to get permission...')

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
        print('Context in detail view before update...: ' + str(context))
        new_context = super(DetailView, self).get_context_data(**context)
        print('New context is: ' + str(new_context))
        return new_context

    def get_template_names(self):
        return 'orders_detail.html'


class CreateView(CreateView):

    def get_form_class(self):
        form_class = super().get_form_class()
        user = self.request.user
        collections = self.permission_helper.permission_policy._collections_with_perm(user, ['add', 'change', 'delete'])
        form_class.base_fields['collection'].queryset = collections
        form_class.base_fields['collection'].choices.queryset = collections

        return form_class


class EditView(EditView):

    def get_form_class(self):
        form_class = super().get_form_class()
        user = self.request.user
        collections = self.permission_helper.permission_policy._collections_with_perm(user, ['add', 'change', 'delete'])
        form_class.base_fields['collection'].queryset = collections
        form_class.base_fields['collection'].choices.queryset = collections

        return form_class


class IndexView(IndexView):

    def get_queryset(self, request=None):
        if 'collection_id' in self.params and self.params.get('collection_id') == '':
            del self.params['collection_id']
        return super().get_queryset(request)

    def get_context_data(self, **kwargs):
        user = self.request.user
        self.collections = self.permission_helper.permission_policy._collections_with_perm(user, ['add', 'change', 'delete'])

        context = {
            'collections': self.collections
        }
        if 'collection_id' in self.params:
            current_collection = Collection.objects.get(id=self.params.get('collection_id'))
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
    permission_helper_class = OrderPermissionHelper

    def get_edit_handler(self, instance, request):
        # print('form_class: ' + str(self.form_class))
        fields_to_exclude = self.get_form_fields_exclude(request=request)
        user = request.user
        collections = self.permission_helper.permission_policy._collections_with_perm(user, ['add', 'change', 'delete'])
        panels = extract_panel_definitions_from_model_class(
            self.model, exclude=fields_to_exclude, collections=collections
        )
        edit_handler = ObjectList(panels)

        return edit_handler

    def get_queryset(self, request):
        """
        This method originally returns all Models of the given model attribute.
        Then it hands them over to the get_queryset functions of all Views
        to apply their own filters. We add an extra step in order to filter
        the results based on the Collections this User has access to.
        """
        user = request.user
        collections = self.permission_helper.permission_policy._collections_with_perm(user, ['add', 'change', 'delete'])
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

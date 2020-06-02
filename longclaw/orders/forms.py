from longclaw.orders.models import Order
from django.forms.models import modelform_factory
from django.utils.translation import gettext as _
from wagtail.admin.forms.collections import (
    BaseCollectionMemberForm, collection_member_permission_formset_factory)


GroupOrderPermissionFormSet = collection_member_permission_formset_factory(
    Order,
    [
        ('add_order', _("Add"), _("Add/edit orders you own")),
        ('change_order', _("Edit"), _("Edit any order")),
    ],
    'orders/permissions/includes/order_permission_formset.html'
)

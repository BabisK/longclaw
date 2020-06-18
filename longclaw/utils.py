from django.apps import apps
from django.utils.module_loading import import_string
from longclaw.settings import PRODUCT_VARIANT_MODEL, PAYMENT_GATEWAY
from wagtail.contrib.modeladmin.helpers import PermissionHelper
from wagtail.core.permission_policies.collections import CollectionPermissionPolicy

GATEWAY = import_string(PAYMENT_GATEWAY)()
ProductVariant = apps.get_model(*PRODUCT_VARIANT_MODEL.split('.'))


def maybe_get_product_model():
    try:
        field = ProductVariant._meta.get_field('product')
        return field.related_model
    except:
        pass


class CustomCollectionPermissionHelper(PermissionHelper):

    def __init__(self, model, inspect_view_enabled=False):
        super().__init__(model, inspect_view_enabled)
        self.permission_policy = CollectionPermissionPolicy(
            model, auth_model=model
        )

    def user_has_permission_for_instance(self, user, action, instance):
        return self.permission_policy.user_has_permission_for_instance(
            user, action, instance
        )

    def user_has_any_permission_for_instance(self, user, actions, instance):
        return self.permission_policy.user_has_any_permission_for_instance(
            user, actions, instance
        )

    def user_has_specific_permission(self, user, action):
        return self.permission_policy.user_has_permission(
            user=user, action=action
        )

    def user_has_any_permissions(self, user):
        return self.permission_policy._check_perm(
            user, actions=['add', 'change', 'delete']
        )

    def user_can_list(self, user):
        return self.user_has_any_permissions(user)

    def user_can_create(self, user):
        return self.user_has_specific_permission(user, action='add')

    def user_can_inspect_obj(self, user, obj):
        inspect_enabled = self.inspect_view_enabled
        return_check = self.user_has_any_permission_for_instance(
            user=user, actions=['add', 'change', 'delete'], instance=obj)

        return inspect_enabled and return_check

    def user_can_edit_obj(self, user, obj):
        return self.user_has_permission_for_instance(
            user, action='change', instance=obj
        )

    def user_can_delete_obj(self, user, obj):
        perm_add = self.user_has_permission_for_instance(
            user, action='add', instance=obj
        )

        perm_change = self.user_has_permission_for_instance(
            user, action='change', instance=obj
        )

        return perm_add and perm_change

from django.contrib.auth import get_permission_codename
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from wagtail.contrib.modeladmin.helpers import PermissionHelper

from wagtail.core.models import Page, UserPagePermissionsProxy
from wagtail.core.permission_policies.collections import CollectionPermissionPolicy
from longclaw.orders.models import Order


class OrderPermissionHelper(PermissionHelper):
    """
    Provides permission-related helper functions to help determine what a
    user can do with a 'typical' model (where permissions are granted
    model-wide), and to a specific instance of that model.
    """

    def __init__(self, model, inspect_view_enabled=False):
        super().__init__(model, inspect_view_enabled)
        self.permission_policy = CollectionPermissionPolicy(
            Order, auth_model=Order
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
        """
        Combine `perm_codename` with `self.opts.app_label` to call the provided
        Django user's built-in `has_perm` method.
        """
        return self.permission_policy.user_has_permission(
            user=user, action=action
        )

    def user_has_any_permissions(self, user):
        return self.permission_policy._check_perm(
            user, actions=['add', 'change', 'delete']
        )

    def user_can_list(self, user):
        """
        Return a boolean to indicate whether `user` is permitted to access the
        list view for self.model
        """
        return self.user_has_any_permissions(user)

    def user_can_create(self, user):
        return self.user_has_specific_permission(user, action='add')

    def user_can_inspect_obj(self, user, obj):
        """
        Return a boolean to indicate whether `user` is permitted to 'inspect'
        a specific `self.model` instance.
        """
        print('We are going to check if user can Inspect object...')
        inspect_enabled = self.inspect_view_enabled
        print('Inspect flag: ' + str(inspect_enabled))
        return_check = self.user_has_any_permission_for_instance(
            user=user, actions=['add', 'change', 'delete'], instance=obj)
        print('permission return value: ' + str(return_check))

        return self.inspect_view_enabled and self.user_has_any_permission_for_instance(
            user=user, actions=['add', 'change', 'delete'], instance=obj)

    def user_can_edit_obj(self, user, obj):
        return self.user_has_permission_for_instance(user, action='change', instance=obj)

    def user_can_delete_obj(self, user, obj):
        return self.user_has_permission_for_instance(user, action='delete', instance=obj)

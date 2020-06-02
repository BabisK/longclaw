from wagtail.core.permission_policies.collections import CollectionPermissionPolicy
from longclaw.shipping.models import ShippingRate

permission_policy = CollectionPermissionPolicy(
    ShippingRate,
    auth_model=ShippingRate
)
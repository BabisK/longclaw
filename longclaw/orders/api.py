from rest_framework.decorators import action
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from longclaw.orders.models import Order
from longclaw.orders.serializers import OrderSerializer
from longclaw.utils import CustomCollectionPermissionHelper


class HasCollectionAccess(permissions.BasePermission):

    permission_helper = CustomCollectionPermissionHelper(
        Order, inspect_view_enabled=True
    )

    def has_object_permission(self, request, view, obj):
        perm_add = self.permission_helper.user_has_permission_for_instance(
            user=request.user, action='add', instance=obj
        )

        perm_change = self.permission_helper.user_has_permission_for_instance(
            user=request.user, action='change', instance=obj
        )

        return perm_add and perm_change

    def has_permission(self, request, view):
        perm_add = self.permission_helper.user_has_specific_permission(
            user=request.user, action='add'
        )

        perm_change = self.permission_helper.user_has_specific_permission(
            user=request.user, action='change'
        )

        return perm_add and perm_change


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [HasCollectionAccess]

    def get_queryset(self):
        permission_obj = self.get_permissions()[0]
        permission_helper = permission_obj.permission_helper
        user = self.request.user
        perm_policy = permission_helper.permission_policy
        collections = perm_policy._collections_with_perm(
            user, ['add', 'change', 'delete']
        )

        return Order.objects.filter(collection__in=collections)

    @action(detail=True, methods=['post'])
    def refund_order(self, request, pk):
        """Refund the order specified by the pk
        """
        order = Order.objects.get(id=pk)
        order.refund()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def fulfill_order(self, request, pk):
        """Mark the order specified by pk as fulfilled
        """
        order = Order.objects.get(id=pk)
        order.fulfill()
        return Response(status=status.HTTP_204_NO_CONTENT)

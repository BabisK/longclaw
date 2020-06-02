# import os

# from django.conf import settings
# from django.core.paginator import Paginator
# from django.http import HttpResponse, JsonResponse
# from django.shortcuts import get_object_or_404, redirect
# from django.template.response import TemplateResponse
# from django.urls import reverse
# from django.urls.exceptions import NoReverseMatch
# from django.utils.translation import gettext as _
# from django.views.decorators.vary import vary_on_headers

# from wagtail.admin import messages
# from wagtail.admin.auth import PermissionPolicyChecker, permission_denied
# from wagtail.admin.forms.search import SearchForm
# from wagtail.core.models import Collection, Site
# from longclaw.orders.permissions import permission_policy
# from longclaw.orders.models import Order
# from longclaw.orders.forms import get_order_form
# from wagtail.search import index as search_index

# permission_checker = PermissionPolicyChecker(permission_policy)

# INDEX_PAGE_SIZE = getattr(settings, 'ORDERS_INDEX_PAGE_SIZE', 20)
# # USAGE_PAGE_SIZE = getattr(settings, 'order_USAGE_PAGE_SIZE', 20)


# @permission_checker.require_any('add', 'change', 'delete')
# @vary_on_headers('X-Requested-With')
# def index(request):

#     # Get orders (filtered by user permission)
#     orders = permission_policy.instances_user_has_any_permission_for(
#         request.user, ['change', 'delete']
#     )

#     # Search
#     query_string = None
#     if 'q' in request.GET:
#         form = SearchForm(request.GET, placeholder=_("Search orders"))
#         if form.is_valid():
#             query_string = form.cleaned_data['q']
#             orders = orders.search(query_string)
#     else:
#         form = SearchForm(placeholder=_("Search orders"))

#     # Filter by collection
#     current_collection = None
#     collection_id = request.GET.get('collection_id')
#     if collection_id:
#         try:
#             current_collection = Collection.objects.get(id=collection_id)
#             orders = orders.filter(collection=current_collection)
#         except (ValueError, Collection.DoesNotExist):
#             pass

#     paginator = Paginator(orders, per_page=INDEX_PAGE_SIZE)
#     orders = paginator.get_page(request.GET.get('p'))

#     collections = permission_policy.collections_user_has_any_permission_for(
#         request.user, ['add', 'change']
#     )
#     if len(collections) < 2:
#         collections = None
#     else:
#         collections = Collection.order_for_display(collections)

#     # Create response
#     if request.is_ajax():
#         return TemplateResponse(request, 'orders/results.html', {
#             'orders': orders,
#             'query_string': query_string,
#             'is_searching': bool(query_string),
#         })
#     else:
#         return TemplateResponse(request, 'orders/index.html', {
#             'orders': orders,
#             'query_string': query_string,
#             'is_searching': bool(query_string),

#             'search_form': form,
#             'collections': collections,
#             'current_collection': current_collection,
#             'user_can_add': permission_policy.user_has_permission(request.user, 'add'),
#         })

#     return TemplateResponse(request, 'orders/index.html', {
#         'orders': orders,
#         'query_string': query_string,
#         'is_searching': bool(query_string),
#         'search_form': form,
#         'collections': collections,
#         'current_collection': current_collection,
#         'user_can_add': permission_policy.user_has_permission(request.user, 'add'),
#     })


# @permission_checker.require('change')
# def edit(request, order_id):
#     OrderForm = get_order_form(Order)

#     order = get_object_or_404(Order, id=order_id)

#     if not permission_policy.user_has_permission_for_instance(request.user, 'change', order):
#         return permission_denied(request)

#     print('Edit is not ready yet')

#     return redirect('orders:index')


# def preview(request, order_id, filter_spec):
#     order = get_object_or_404(Order, id=order_id)
#     response = HttpResponse('Preview is not ready')
#     return response


# @permission_checker.require('delete')
# def delete(request, order_id):
#     order = get_object_or_404(Order, id=order_id)

#     if not permission_policy.user_has_permission_for_instance(request.user, 'delete', order):
#         return permission_denied(request)

#     if request.method == 'POST':
#         order.delete()
#         messages.success(request, _("Order '{0}' deleted.").format(order.id))
#         return redirect('orders:index')

#     return TemplateResponse(request, "orders/confirm_delete.html", {
#         'order': order,
#     })


# @permission_checker.require('add')
# def add(request):
#     OrderForm = get_order_form(Order)

#     if request.method == 'POST':
#         print('You send a POST request to the Create Order Form!')
#         order = Order()
#         form = OrderForm(request.POST, request.FILES, instance=order, user=request.user)
#         # if form.is_valid():
#         #     # Set image file size
#         #     # image.file_size = order.file.size

#         #     # # Set image file hash
#         #     # image.file.seek(0)
#         #     # image._set_file_hash(image.file.read())
#         #     # image.file.seek(0)

#         #     form.save()

#         #     # Reindex the image to make sure all tags are indexed
#         #     search_index.insert_or_update_object(order)

#         #     messages.success(request, _("Order '{0}' added.").format(order.title), buttons=[
#         #         messages.button(reverse('orders:edit', args=(order.id,)), _('Edit'))
#         #     ])
#         return redirect('orders:index')
#         # else:
#         #     messages.error(request, _("The order could not be created due to errors."))
#     else:
#         form = OrderForm(user=request.user)

#     return TemplateResponse(request, "orders/add.html", {
#         'form': form,
#     })
from django.db import models
from wagtail.core.models import Page, CollectionMember

from django.utils.translation import gettext_lazy as _
from wagtail.core.models import Collection, get_root_collection_id
from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.core.permission_policies.collections import \
    CollectionPermissionPolicy
from django.contrib.auth.models import User


class ProductWithCollectionPageForm(WagtailAdminPageForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user_id = self.instance.owner_id
        user = User.objects.get(pk=user_id)

        if user.is_active and user.is_authenticated and not user.is_superuser:
            permission_policy = CollectionPermissionPolicy(
                model=type(self.instance), auth_model=type(self.instance)
            )

            collections_permitted = permission_policy._collections_with_perm(
                user, ['add', 'change', 'delete']
            )
            self.fields['collection'].choices.queryset = collections_permitted
            self.fields['collection'].queryset = collections_permitted


# Abstract base classes a user can use to implement their own product system
class ProductBase(Page):
    """Base classes for ``Product`` implementations. All this provides are
    a few helper methods for ``ProductVariant``'s. It assumes that ``ProductVariant``'s
    have a ``related_name`` of ``variants``
    """

    class Meta:
        abstract = True

    def __str__(self):
        return self.title

    @property
    def price_range(self):
        """ Calculate the price range of the products variants
        """
        ordered = self.variants.order_by('base_price')
        if ordered:
            return ordered.first().price, ordered.last().price
        else:
            return None, None

    @property
    def in_stock(self):
        """ Returns True if any of the product variants are in stock
        """
        return any(self.variants.filter(stock__gt=0))


class ProductWithCollectionBase(CollectionMember, ProductBase):
    collection = models.ForeignKey(
        Collection,
        default=get_root_collection_id,
        verbose_name=_('collection'),
        related_name='+',
        on_delete=models.PROTECT
    )
    base_form_class = ProductWithCollectionPageForm


class ProductVariantBase(models.Model):
    """
    Base model for creating product variants
    """
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    ref = models.CharField(max_length=32)
    stock = models.IntegerField(default=0)

    class Meta:
        abstract = True

    def __str__(self):
        try:
            return "{} - {}".format(self.product.title, self.ref)
        except AttributeError:
            return self.ref

    @property
    def price(self):
        """Can be overridden in concrete implementations in
        order to generate the price dynamically.

        Override the property like so:

            @ProductVariantBase.price.getter
            def price(self):
              ...

        """
        return self.base_price

    def get_product_title(self):
        """Retrieve the title of the related product.
        If no related product, just return the ``ref`` of this model
        """
        try:
            return self.product.title
        except AttributeError:
            return self.ref

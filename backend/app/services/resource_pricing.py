"""Shared resource pricing rules."""

from decimal import Decimal


def is_free_resource(resource) -> bool:
    """Return whether a resource can be accessed without a purchase.

    ``is_free`` remains the primary flag. The zero-price fallback keeps
    legacy rows with both monetary and coin prices set to zero consistent
    across access and order creation, without making an old paid row free
    just because its coin price is missing.
    """
    if resource.is_free:
        return True

    coin_price = resource.coin_price or 0
    monetary_price = resource.price or Decimal("0")
    return coin_price == 0 and monetary_price == 0

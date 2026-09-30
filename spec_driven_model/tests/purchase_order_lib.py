# file generated using:
# xsdata generate spec_driven_model/tests/PurchaseOrderSchema.xsd

from dataclasses import dataclass, field
from decimal import Decimal

from xsdata.models.datatype import XmlDate

__NAMESPACE__ = "http://tempuri.org/PurchaseOrderSchema.xsd"


@dataclass
class Items:
    item: list["Items.Item"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
        },
    )

    @dataclass
    class Item:
        product_name: str | None = field(
            default=None,
            metadata={
                "name": "productName",
                "type": "Element",
                "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
                "required": True,
            },
        )
        quantity: int | None = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
                "required": True,
                "min_inclusive": 1,
                "max_exclusive": 100,
            },
        )
        usprice: Decimal | None = field(
            default=None,
            metadata={
                "name": "USPrice",
                "type": "Element",
                "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
                "required": True,
            },
        )
        comment: str | None = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
                "required": True,
            },
        )
        ship_date: XmlDate | None = field(
            default=None,
            metadata={
                "name": "shipDate",
                "type": "Element",
                "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
            },
        )
        part_num: str | None = field(
            default=None,
            metadata={
                "name": "partNum",
                "type": "Attribute",
                "pattern": r"\d{3}\w{3}",
            },
        )


@dataclass
class Usaddress:
    """
    Purchase order schema for Example.Microsoft.com.
    """

    class Meta:
        name = "USAddress"

    name: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
            "required": True,
        },
    )
    street: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
            "required": True,
        },
    )
    city: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
            "required": True,
        },
    )
    state: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
            "required": True,
        },
    )
    zip: Decimal | None = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
            "required": True,
        },
    )
    country: str = field(
        init=False,
        default="US",
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class Comment:
    class Meta:
        name = "comment"
        namespace = "http://tempuri.org/PurchaseOrderSchema.xsd"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )


@dataclass
class PurchaseOrderType:
    ship_to: Usaddress | None = field(
        default=None,
        metadata={
            "name": "shipTo",
            "type": "Element",
            "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
            "required": True,
        },
    )
    bill_to: Usaddress | None = field(
        default=None,
        metadata={
            "name": "billTo",
            "type": "Element",
            "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
            "required": True,
        },
    )
    comment: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
        },
    )
    items: Items | None = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
            "required": True,
        },
    )
    order_date: XmlDate | None = field(
        default=None,
        metadata={
            "name": "orderDate",
            "type": "Attribute",
        },
    )
    confirm_date: XmlDate | None = field(
        default=None,
        metadata={
            "name": "confirmDate",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class PurchaseOrder(PurchaseOrderType):
    class Meta:
        name = "purchaseOrder"
        namespace = "http://tempuri.org/PurchaseOrderSchema.xsd"

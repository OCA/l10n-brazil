# file generated using:
# xsdata generate spec_driven_model/tests/PurchaseOrderSchema.xsd

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional
from xsdata.models.datatype import XmlDate

__NAMESPACE__ = "http://tempuri.org/PurchaseOrderSchema.xsd"


@dataclass
class Items:
    item: List["Items.Item"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
        }
    )

    @dataclass
    class Item:
        product_name: Optional[str] = field(
            default=None,
            metadata={
                "name": "productName",
                "type": "Element",
                "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
                "required": True,
            }
        )
        quantity: Optional[int] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
                "required": True,
                "min_inclusive": 1,
                "max_exclusive": 100,
            }
        )
        usprice: Optional[Decimal] = field(
            default=None,
            metadata={
                "name": "USPrice",
                "type": "Element",
                "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
                "required": True,
            }
        )
        comment: Optional[str] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
                "required": True,
            }
        )
        ship_date: Optional[XmlDate] = field(
            default=None,
            metadata={
                "name": "shipDate",
                "type": "Element",
                "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
            }
        )
        part_num: Optional[str] = field(
            default=None,
            metadata={
                "name": "partNum",
                "type": "Attribute",
                "pattern": r"\d{3}\w{3}",
            }
        )


@dataclass
class Usaddress:
    """
    Purchase order schema for Example.Microsoft.com.
    """
    class Meta:
        name = "USAddress"

    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
            "required": True,
        }
    )
    street: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
            "required": True,
        }
    )
    city: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
            "required": True,
        }
    )
    state: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
            "required": True,
        }
    )
    zip: Optional[Decimal] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
            "required": True,
        }
    )
    country: str = field(
        init=False,
        default="US",
        metadata={
            "type": "Attribute",
        }
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
        }
    )


@dataclass
class PurchaseOrderType:
    ship_to: Optional[Usaddress] = field(
        default=None,
        metadata={
            "name": "shipTo",
            "type": "Element",
            "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
            "required": True,
        }
    )
    bill_to: Optional[Usaddress] = field(
        default=None,
        metadata={
            "name": "billTo",
            "type": "Element",
            "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
            "required": True,
        }
    )
    comment: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
        }
    )
    items: Optional[Items] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://tempuri.org/PurchaseOrderSchema.xsd",
            "required": True,
        }
    )
    order_date: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "orderDate",
            "type": "Attribute",
        }
    )
    confirm_date: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "confirmDate",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass
class PurchaseOrder(PurchaseOrderType):
    class Meta:
        name = "purchaseOrder"
        namespace = "http://tempuri.org/PurchaseOrderSchema.xsd"

# this file a relevant subset of a Python binding that is generated using
# a code generator with the xsd schema PurchaseOrderSchema.xsd
# for instance with GenerateDS one would do:
# /usr/local/bin/generateDS --no-namespace-defs --no-dates --member-specs="list"\
# --use-getter-setter="none" -o "purchase_order_lib.py" PurchaseOrderSchema.xsd
# GenerateDS files are very verbose and don't enforce OCA standards, that is
# why only the relevant subset has been copied here (without the XML import/export).
# We also do that because we don't want spec_model_driven too much coupled
# with a specific XSD databinding tool.


class MemberSpec_(object):
    def __init__(
        self,
        name="",
        data_type="",
        container=0,
        optional=0,
        child_attrs=None,
        choice=None,
    ):
        self.name = name
        self.data_type = data_type
        self.container = container
        self.child_attrs = child_attrs
        self.choice = choice
        self.optional = optional

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def set_data_type(self, data_type):
        self.data_type = data_type

    def get_data_type_chain(self):
        return self.data_type

    def get_data_type(self):
        if isinstance(self.data_type, list):
            if len(self.data_type) > 0:
                return self.data_type[-1]
            else:
                return "xs:string"
        else:
            return self.data_type

    def set_container(self, container):
        self.container = container

    def get_container(self):
        return self.container

    def set_child_attrs(self, child_attrs):
        self.child_attrs = child_attrs

    def get_child_attrs(self):
        return self.child_attrs

    def set_choice(self, choice):
        self.choice = choice

    def get_choice(self):
        return self.choice

    def set_optional(self, optional):
        self.optional = optional

    def get_optional(self):
        return self.optional


def _cast(typ, value):
    if typ is None or value is None:
        return value
    return typ(value)


class USAddress(object):
    """Purchase order schema for Example.Microsoft.com."""

    member_data_items_ = [
        MemberSpec_("country", "xsd:NMTOKEN", 0, 1, {"use": "optional"}),
        MemberSpec_(
            "name", "xsd:string", 0, 0, {"name": "name", "type": "xsd:string"}, None
        ),
        MemberSpec_(
            "street", "xsd:string", 0, 0, {"name": "street", "type": "xsd:string"}, None
        ),
        MemberSpec_(
            "city", "xsd:string", 0, 0, {"name": "city", "type": "xsd:string"}, None
        ),
        MemberSpec_(
            "state", "xsd:string", 0, 0, {"name": "state", "type": "xsd:string"}, None
        ),
        MemberSpec_(
            "_zip", "xsd:decimal", 0, 0, {"name": "_zip", "type": "xsd:decimal"}, None
        ),
    ]

    def __init__(
        self,
        country="US",
        name=None,
        street=None,
        city=None,
        state=None,
        _zip=None,  # changed zip to _zip to make pylint happy
        gds_collector_=None,
        **kwargs_
    ):
        self.country = _cast(None, country)
        self.country_nsprefix_ = None
        self.name = name
        self.name_nsprefix_ = None
        self.street = street
        self.street_nsprefix_ = None
        self.city = city
        self.city_nsprefix_ = None
        self.state = state
        self.state_nsprefix_ = None
        self._zip = _zip
        self.zip_nsprefix_ = None


class Items(object):
    member_data_items_ = [
        MemberSpec_(
            "item",
            "ItemType",
            1,
            1,
            {
                "maxOccurs": "unbounded",
                "minOccurs": "0",
                "name": "item",
                "type": "ItemType",
            },
            None,
        ),
    ]

    def __init__(self, item=None, gds_collector_=None, **kwargs_):
        if item is None:
            self.item = []
        else:
            self.item = item
        self.item_nsprefix_ = None


class PurchaseOrderType(object):
    member_data_items_ = [
        MemberSpec_("orderDate", "xsd:date", 0, 1, {"use": "optional"}),
        MemberSpec_("confirmDate", "xsd:date", 0, 0, {"use": "required"}),
        MemberSpec_(
            "shipTo", "USAddress", 0, 0, {"name": "shipTo", "type": "USAddress"}, None
        ),
        MemberSpec_(
            "billTo", "USAddress", 0, 0, {"name": "billTo", "type": "USAddress"}, None
        ),
        MemberSpec_(
            "comment",
            "xsd:string",
            0,
            1,
            {
                "minOccurs": "0",
                "name": "comment",
                "ref": "comment",
                "type": "xsd:string",
            },
            None,
        ),
        MemberSpec_("items", "Items", 0, 0, {"name": "items", "type": "Items"}, None),
    ]

    def __init__(
        self,
        orderDate=None,
        confirmDate=None,
        shipTo=None,
        billTo=None,
        comment=None,
        items=None,
        gds_collector_=None,
        **kwargs_
    ):
        initvalue_ = orderDate
        self.orderDate = initvalue_
        self.confirmDate = confirmDate
        self.shipTo = shipTo
        self.shipTo_nsprefix_ = None
        self.billTo = billTo
        self.billTo_nsprefix_ = None
        self.comment = comment
        self.comment_nsprefix_ = None
        self.items = items
        self.items_nsprefix_ = None


class ItemType(object):  # changed itemType to ItemType to make pylint happy
    member_data_items_ = [
        MemberSpec_("partNum", "tns:SKU", 0, 1, {"use": "optional"}),
        MemberSpec_(
            "productName",
            "xsd:string",
            0,
            0,
            {"name": "productName", "type": "xsd:string"},
            None,
        ),
        MemberSpec_(
            "quantity",
            ["quantityType", "xsd:positiveInteger"],
            0,
            0,
            {"name": "quantity", "type": "xsd:positiveInteger"},
            None,
        ),
        MemberSpec_(
            "USPrice",
            "xsd:decimal",
            0,
            0,
            {"name": "USPrice", "type": "xsd:decimal"},
            None,
        ),
        MemberSpec_(
            "comment",
            "xsd:string",
            0,
            0,
            {"name": "comment", "ref": "comment", "type": "xsd:string"},
            None,
        ),
        MemberSpec_(
            "shipDate",
            "xsd:date",
            0,
            1,
            {"minOccurs": "0", "name": "shipDate", "type": "xsd:date"},
            None,
        ),
    ]

    def __init__(
        self,
        partNum=None,
        productName=None,
        quantity=None,
        USPrice=None,
        comment=None,
        shipDate=None,
        gds_collector_=None,
        **kwargs_
    ):
        self.partNum = _cast(None, partNum)
        self.partNum_nsprefix_ = None
        self.productName = productName
        self.productName_nsprefix_ = None
        self.quantity = quantity
        self.quantity_nsprefix_ = None
        self.USPrice = USPrice
        self.USPrice_nsprefix_ = None
        self.comment = comment
        self.comment_nsprefix_ = None
        self.shipDate = shipDate
        self.shipDate_nsprefix_ = None

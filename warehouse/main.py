from __future__ import annotations


from typing import List


class NotEnoughQuantityError(Exception):
    pass


class Address:

    def __init__(self, city: str, street: str, building: str):
        self.city = city
        self.street = street
        self.building = building


class Product:

    def __init__(self, sku: str, name: str, price: float):
        self.sku = sku
        self.name = name
        self.price = price


class ProductStock:

    def __init__(self, product: Product, quantity: int, warehouse: Warehouse):
        self.product = product
        self.quantity = quantity
        self.warehouse = warehouse

    def increase_quantity(self, quantity: int):
        self.quantity += quantity

    def decrease_quantity(self, quantity: int):
        self.quantity -= quantity


class ProductReserve:
    NEW = 'NEW'
    COMPLETED = 'COMPLETED'
    CANCELED = 'CANCELED'

    def __init__(self, order: Order, product: Product, quantity: int, warehouse: Warehouse):
        self.order = order
        self.product = product
        self.quantity = quantity
        self.warehouse = warehouse
        self.status = self.NEW

    def make_completed(self):
        self.status = self.COMPLETED
        self.order.start_delivering()

    def make_canceled(self):
        self.warehouse.add_product_stock(self.product, self.quantity)
        self.status = self.CANCELED


class Warehouse:
    WAREHOUSES = []

    def __init__(self, name: str, address: Address):
        self.name = name
        self.address = address
        self._product_stock_list: List[ProductStock] = []
        self.WAREHOUSES.append(self)

    @classmethod
    def get_warehouse(cls, address: Address) -> Warehouse:
        for warehouse in cls.WAREHOUSES:
            if warehouse.address.city == address.city:
                return warehouse

    def add_product_stock(self, product: Product, quantity: int) -> None:
        updated = False
        for stock in self._product_stock_list:
            if stock.product == product:
                stock.increase_quantity(quantity)
                updated = True
                break
        if not updated:
            self._product_stock_list.append(ProductStock(product, quantity, self))

    def get_product_stock(self, product: Product) -> ProductStock:
        return next(
            (product_stock for product_stock in self._product_stock_list if product_stock.product == product),
            None
        )

    def reserve_product(self, product: Product, quantity: int, order: Order) -> ProductReserve:
        product_stock = self.get_product_stock(product)
        if product_stock.quantity < quantity:
            raise NotEnoughQuantityError('Not enough products in stock')
        product_stock.decrease_quantity(quantity)
        return ProductReserve(order, product, quantity, self)


class ReserveMoving:
    NEW = 'NEW'
    DELIVERING = 'DELIVERING'
    FINISHED = 'FINISHED'

    def __init__(self, reserve: ProductReserve, warehouse: Warehouse):
        self.reserve = reserve
        self.warehouse = warehouse
        self.status = self.NEW

    def start_deliver(self):
        self.status = self.DELIVERING

    def make_finished(self):
        self.reserve.warehouse = self.reserve.warehouse
        self.status = self.FINISHED


class Item:

    def __init__(self, product: Product, quantity: int):
        self.product = product
        self.quantity = quantity


class Order:
    NEW = 'NEW'
    COMPLETING = 'COMPLETING'
    DELIVERING = 'DELIVERING'
    FINISHED = 'FINISHED'

    def __init__(self, address: Address):
        self.address = address
        self.items: List[Item] = []
        self.status = self.NEW
        self.warehouse = Warehouse.get_warehouse(address)
        self.WAREHOUSES = iter([w for w in Warehouse.WAREHOUSES if w != self.warehouse])
        self._reserves: List[ProductReserve] = []

    def add_product(self, product: Product, quantity: int) -> None:
        self.items.append(Item(product, quantity))

    def get_price(self) -> float:
        return sum(item.product.price * item.quantity for item in self.items)

    def start_completing(self) -> None:
        for item in self.items:
            reserve = self._reserve_product(item.product, item.quantity, self.warehouse)
            self._reserves.append(reserve)
        self.status = self.COMPLETING

    def start_delivering(self) -> None:
        if all(reserve.status == ProductReserve.COMPLETED for reserve in self._reserves):
            self.status = self.DELIVERING

    def _reserve_product(self, product: Product, quantity: int, warehouse: Warehouse) -> ProductReserve:
        stock = warehouse.get_product_stock(product)
        if stock.quantity >= quantity:
            reserve = warehouse.reserve_product(product, quantity, self)
            return reserve
        else:
            left_quantity = quantity - stock.quantity
            try:
                warehouse = next(self.warehouses)
                return self._reserve_product(product, warehouse, left_quantity)
            except StopIteration:
                raise NotEnoughQuantityError('Not enough products in stock')

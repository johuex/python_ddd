from typing import List


class OutOfStock(Exception):
    def __init__(self, line_sku: str):
        self.line_sku = line_sku
        self.message = 'No available Batch for order {}'
        super().__init__(self.message)

    def __str__(self):
        return self.message.format(self.line_sku)


class NoOrderInBatch(Exception):
    def __init__(self, line_id: str, line_sku: str, batches_sku: List[str]):
        self.line_sku = line_sku
        self.line_id = line_id
        self.batches_sku = batches_sku
        self.message = "No order line {}:{} in batches {}"
        super().__init__(self.message)

    def __str__(self):
        return self.message.format(self.line_id, self.line_sku, self.batches_sku)


class InvalidSku(Exception):
    def __init__(self, sku: str):
        self.sku = sku
        self.message = 'Invalid stock-keeping: {}'
        super().__init__(self.message)

    def __str__(self):
        return self.message.format(self.sku)

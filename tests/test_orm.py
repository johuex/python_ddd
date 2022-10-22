from models import domain_models


class TestOrm:

    def test_orderline_mapper_can_load_lines(self, db_session):
        db_session.execute(
            'INSERT INTO order_lines (orderid, sku, qty) VALUES '
            '("order1", "RED-CHAIR", 12),'
            '("order1", "RED-TABLE", 13),'
            '("order2", "BLUE-LIPSTICK", 14)'
        )
        expected = [
            domain_models.OrderLine("order1", "RED-CHAIR", 12),
            domain_models.OrderLine("order1", "RED-TABLE", 13),
            domain_models.OrderLine("order2", "BLUE-LIPSTICK", 14),
        ]
        assert db_session.query(domain_models.OrderLine).all() == expected

    def test_orderline_mapper_can_save_lines(self, db_session):
        new_line = domain_models.OrderLine("order1", "DECORATIVE-WIDGET", 12)
        db_session.add(new_line)
        db_session.commit()
        rows = list(db_session.execute('SELECT orderid, sku, qty FROM"order_lines"'))
        assert rows == [("order1", "DECORATIVE-WIDGET", 12)]

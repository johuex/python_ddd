from src.allocation.models import domain_models


class TestOrm:

    def test_orderline_mapper_can_load_lines(self, sqlite_session):
        """
        1. В БД сырым запросом делаем INSERT данных
        2. Делаем query через ORM-запрос
        ОР: expected и данные из ORM-запроса совпали
        """
        sqlite_session.execute(
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
        assert sqlite_session.query(domain_models.OrderLine).all() == expected

    def test_orderline_mapper_can_save_lines(self, sqlite_session):
        """
        1. Добавляем товарную позицию в БД
        2. Делаем коммит
        3. Делаем SELECT через RM
        ОР: Полученное в SELECT совпадает с ожидаемым
        """
        new_line = domain_models.OrderLine("order1", "DECORATIVE-WIDGET", 12)
        sqlite_session.add(new_line)
        sqlite_session.commit()
        rows = list(sqlite_session.execute('SELECT orderid, sku, qty FROM"order_lines"'))
        assert rows == [("order1", "DECORATIVE-WIDGET", 12)]

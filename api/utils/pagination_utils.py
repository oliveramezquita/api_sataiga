# api/utils/pagination_utils.py
class DummyPaginator:
    """
    Simula el comportamiento mínimo del Paginator de Django
    para integrarse con build_response_with_pagination().
    """

    def __init__(self, total, total_pages):
        self.count = total
        self.num_pages = total_pages

    def page_range(self):
        return range(1, self.num_pages + 1)


class DummyPage:
    """
    Simula un objeto Page del Paginator de Django,
    compatible con has_next(), len(), iter() y demás.
    """

    def __init__(self, number, paginator, object_list):
        self.number = number
        self.paginator = paginator
        self.object_list = object_list  # ⚠️ necesario para len() e iter()

    # Métodos esperados por build_response_with_pagination
    def has_next(self):
        return self.number < self.paginator.num_pages

    def has_previous(self):
        return self.number > 1

    def has_other_pages(self):
        return self.paginator.num_pages > 1

    # Permiten que len(page) e iter(page) funcionen correctamente
    def __len__(self):
        return len(self.object_list)

    def __iter__(self):
        return iter(self.object_list)

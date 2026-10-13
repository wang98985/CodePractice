from rest_framework.pagination import PageNumberPagination


class ManagePagination(PageNumberPagination):
    """管理端列表分页：默认 20 条/页，可通过 page_size 调整（上限 200）"""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 200
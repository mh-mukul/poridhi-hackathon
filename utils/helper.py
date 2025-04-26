class ResponseHelper:
    def success_response(self, status_code, message, data=None):
        return ({
            "status": status_code,
            "message": message,
            "data": data
        })

    def error_response(self, status_code, message, data=None):
        return ({
            "status": status_code,
            "message": message,
            "data": data
        })


def sort_by_index(items, index_list):
    """
    Sort items based on the provided index list.

    Args:
        items (list): List of items to sort.
        index_list (list): List of indices specifying the new order.

    Returns:
        list: Sorted list of items.
    """
    return [items[i] for i in index_list]

from backend_main.types.request import Request, request_connection_key, request_transaction_key


async def start_transaction(request: Request) -> None:
    """ Starts a transaction and adds it to request, if there is currently no active transaction in `request` storage. """
    if request_transaction_key in request:
        if request[request_transaction_key].is_active:
            return

    request[request_transaction_key] = await request[request_connection_key].begin()

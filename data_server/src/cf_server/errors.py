
class RetrieverRequestError(Exception):
    def __init__(self, descr: str = ""):
        super().__init__(f"Data retrieval failed: the retriever could not retrieve the requested data. {descr}")


class GeneralInternalServerError(Exception):
    def __init__(self, descr: str = ""):
        super().__init__(f"General internal server error. {descr}")

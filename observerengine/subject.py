# =====================================
# ORDER SUBJECT
# =====================================

class OrderSubject:


    def __init__(self):

        self.observers = []


    # =====================================
    # REGISTER
    # =====================================

    def register(

        self,
        observer

    ):

        self.observers.append(

            observer

        )


    # =====================================
    # NOTIFY
    # =====================================

    def notify(

        self,
        data

    ):

        for observer in self.observers:

            observer.update(

                data

            )
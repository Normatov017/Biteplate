# =====================================
# OBSERVER
# =====================================

class Observer:

    def update(

        self,
        data

    ):

        raise NotImplementedError


# =====================================
# WAITER OBSERVER
# =====================================

class WaiterObserver(

    Observer

):

    def update(

        self,
        data

    ):

        print(

            'Waiter Notification:',

            data

        )


# =====================================
# MANAGER OBSERVER
# =====================================

class ManagerObserver(

    Observer

):

    def update(

        self,
        data

    ):

        print(

            'Manager Notification:',

            data

        )


# =====================================
# KITCHEN OBSERVER
# =====================================

class KitchenObserver(

    Observer

):

    def update(

        self,
        data

    ):

        print(

            'Kitchen Notification:',

            data

        )
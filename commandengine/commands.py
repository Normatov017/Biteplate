from abc import ABC
from abc import abstractmethod


# =====================================
# BASE COMMAND
# =====================================

class Command(ABC):

    @abstractmethod
    def execute(self):

        raise NotImplementedError


    @abstractmethod
    def undo(self):

        raise NotImplementedError


# =====================================
# PREPARE ORDER COMMAND
# =====================================

class PrepareOrderCommand(

    Command

):

    def __init__(

        self,
        order

    ):

        self.order = order
        self.previous_status = None
        self.previous_kitchen_status = None


    def execute(self):

        self.previous_status = self.order.status
        self.previous_kitchen_status = self.order.kitchen_status
        self.order.status = 'preparing'
        self.order.kitchen_status = 'preparing'

        self.order.save()


    def undo(self):

        self.order.status = self.previous_status or 'pending'
        self.order.kitchen_status = self.previous_kitchen_status or 'waiting'

        self.order.save()


# =====================================
# READY ORDER COMMAND
# =====================================

class ReadyOrderCommand(

    Command

):

    def __init__(

        self,
        order

    ):

        self.order = order
        self.previous_status = None
        self.previous_kitchen_status = None


    def execute(self):

        self.previous_status = self.order.status
        self.previous_kitchen_status = self.order.kitchen_status
        self.order.status = 'ready'
        self.order.kitchen_status = 'ready'

        self.order.save()


    def undo(self):

        self.order.status = self.previous_status or 'preparing'
        self.order.kitchen_status = self.previous_kitchen_status or 'preparing'

        self.order.save()


# =====================================
# CANCEL ORDER COMMAND
# =====================================

class CancelOrderCommand(

    Command

):

    def __init__(

        self,
        order

    ):

        self.order = order
        self.previous_status = None
        self.previous_kitchen_status = None


    def execute(self):

        self.previous_status = self.order.status
        self.previous_kitchen_status = self.order.kitchen_status
        self.order.status = 'cancelled'
        self.order.kitchen_status = 'cancelled'

        self.order.save()


    def undo(self):

        self.order.status = self.previous_status or 'pending'
        self.order.kitchen_status = self.previous_kitchen_status or 'waiting'

        self.order.save()

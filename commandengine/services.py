# =====================================
# KITCHEN QUEUE
# =====================================

class KitchenQueue:


    def __init__(self):

        self.history = []


    def run(

        self,
        command

    ):

        command.execute()

        self.history.append(

            command

        )


    def undo_last(self):

        if self.history:

            command = self.history.pop()

            command.undo()


    def reprioritize(
        self,
        orders
    ):

        return sorted(
            orders,
            key=lambda order: (
                -getattr(order, 'priority', 0),
                getattr(order, 'created_at', None)
            )
        )

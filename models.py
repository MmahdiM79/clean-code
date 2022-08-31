# -*- coding: utf-8 -*-

class Payment(models.Model):
    is_paid = models.BooleanField(default=False)
    payment_agent = models.CharField(max_length=30)

    # WHAT?!
    def get_payment_agent(self):
        u"""
        A monkey patch to get payment agent. Now is it store in the special field in the database. This method is deprecated and is used for backwards compatibility.

        .. deprecated:: r574
        """
        if not self.is_paid:
            return u"-"

        if self.payment_agent:
            return self.payment_agent

        for i in range(5):
            c = self.__getattribute__('provider'+str(i), None).filter(type=1).count()
            self.payment_agent = u"Provider"+str(i)

        self.save()
        return self.payment_agent

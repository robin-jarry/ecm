# Copyright (c) 2010-2011 Robin Jarry
# 
# This file is part of EVE Corporation Management.
# 
# EVE Corporation Management is free software: you can redistribute it and/or 
# modify it under the terms of the GNU General Public License as published by 
# the Free Software Foundation, either version 3 of the License, or (at your 
# option) any later version.
# 
# EVE Corporation Management is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY 
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for 
# more details.
# 
# You should have received a copy of the GNU General Public License along with 
# EVE Corporation Management. If not, see <http://www.gnu.org/licenses/>.

__date__ = "2011 6 7"
__author__ = "diabeteman"

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

#------------------------------------------------------------------------------
class Order(models.Model):
    
    SUBMITTED = 0
    CANCELED = 1
    REJECTED_BY_MANUFACTURER = 2
    ON_HOLD = 3
    IN_PREPARATION = 4
    READY = 5
    DELIVERED = 6
    REJECTED_BY_CLIENT = 7
    PAID = 8
    
    STATES = {
        SUBMITTED : _('Submitted'),
        CANCELED : _('Canceled'),
        REJECTED_BY_MANUFACTURER : _('Rejected by Manufacturer'),
        ON_HOLD : _('On Hold'),
        IN_PREPARATION : _('In Preparation'),
        READY : _('Ready'),
        DELIVERED : _('Delivered'),
        REJECTED_BY_CLIENT : _('Rejected by Client'),
        PAID : _('Paid'),
    }
    
    TRANSITIONS = {
        SUBMITTED : (CANCELED, REJECTED_BY_MANUFACTURER, ON_HOLD, IN_PREPARATION),
        CANCELED : (),
        REJECTED_BY_MANUFACTURER : (),
        ON_HOLD : (CANCELED, IN_PREPARATION),
        IN_PREPARATION : (READY),
        READY : (DELIVERED),
        DELIVERED : (REJECTED_BY_CLIENT, PAID),
        REJECTED_BY_CLIENT : (),
        PAID : (),
    }
    
    originator = models.ForeignKey(User)
    manufacturer = models.ForeignKey(User, null=True, blank=True)
    deliveryMan = models.ForeignKey(User, null=True, blank=True)
    client = models.CharField(max_length=256, null=True, blank=True)
    deliveryLocation = models.CharField(max_length=256, null=True, blank=True)
    deliveryDate = models.DateField(null=True, blank=True)
    nature = models.ForeignKey('OrderNature')
    site = models.ForeignKey('ProductionSite')
    state = models.PositiveIntegerField(default=SUBMITTED)
    discount = models.FloatField(default=0.0)
    quote = models.FloatField(null=True, blank=True)
    
    def changeState(self, state):
        if state not in Order.TRANSITIONS[state]:
            legalStates = str([ Order.STATES[s] for s in Order.TRANSITIONS[state] ])
            raise IllegalStateError(Order.STATES[state]+' is illegal. Only '+legalStates+' are allowed.')
        self.state = state
    
    #############################
    # TRANSISTIONS
    
    def cancel(self, reason):
        self.changeState(Order.CANCELED)
        self.comments.create(order=self, user=self.originator, text=str(reason))
        self.save()
        
    def rejectByManufacturer(self, manufacturer, reason):
        assert isinstance(manufacturer, User)
        self.changeState(Order.REJECTED_BY_MANUFACTURER)
        self.manufacturer = manufacturer
        self.comments.create(order=self, user=self.manufacturer, text=str(reason))
        self.save()
    
    def startPreparation(self, manufacturer):
        assert isinstance(manufacturer, User)
        self.changeState(Order.IN_PREPARATION)
        self.manufacturer = manufacturer
        self.save()
    
    def endPreparation(self):
        self.changeState(Order.READY)
        self.save()
    
    def deliver(self, deliveryMan):
        assert isinstance(deliveryMan, User)
        self.changeState(Order.DELIVERED)
        self.deliveryMan = deliveryMan
        self.save()
        
    def pay(self):
        self.changeState(Order.PAID)
        self.save()
        
    def rejectByClient(self, reason):
        self.changeState(Order.REJECTED_BY_CLIENT)
        self.comments.create(order=self, user=self.deliveryMan, text=str(reason))
        self.save()

#------------------------------------------------------------------------------
class Comment(models.Model):
    
    order = models.ForeignKey(Order, related_name='comments')
    user = models.ForeignKey(User, related_name='comments')
    text = models.TextField()
    
#------------------------------------------------------------------------------
class OrderRow(models.Model):
    
    typeID = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()
    order = models.ForeignKey(Order, related_name='rows')

#------------------------------------------------------------------------------
class NeededMaterial(models.Model):
    
    order = models.ForeignKey(Order, related_name='materials')
    typeID = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()

#------------------------------------------------------------------------------
class OrderState(models.Model):
    
    name = models.CharField(max_length=256)
    
#------------------------------------------------------------------------------
class OrderNature(models.Model):
    
    name = models.CharField(max_length=256)

#------------------------------------------------------------------------------
class ProductionSite(models.Model):
    
    locationID = models.PositiveIntegerField(primary_key=True)
    customName = models.CharField(max_length=256)
    natures = models.ManyToManyField(OrderNature, related_name='sites')
    discount = models.FloatField(default=0.0)
    

#------------------------------------------------------------------------------
class OwnedBlueprint(models.Model):
    
    typeID = models.PositiveIntegerField(primary_key=True)
    count = models.PositiveIntegerField()
    original = models.BooleanField(default=True)
    me = models.PositiveIntegerField()
    pe = models.PositiveIntegerField()
    
    
    
    def getItem(self):
        pass
    
    def getBlueprint(self):
        pass
    
    def getBillOfMaterials(self, customMe=None, customPe=None):
        pass
    
    
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------ 
class IllegalStateError(UserWarning):
    pass
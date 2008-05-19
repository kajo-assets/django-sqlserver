from django.db import models

class TableNullText(models.Model):
	amount = models.TextField(null=True)
	
	def __unicode__(self):
		return u'id: ' + unicode(self.id) + ' Amount: ' + unicode(self.amount)
		
class TableNullInteger(models.Model):
	amount = models.IntegerField(null=True)
	
	def __unicode__(self):
		return u'id: ' + unicode(self.id) + ' Amount: ' + unicode(self.amount)

class TableNullDateTime(models.Model):
	amount = models.DateTimeField(null=True)
	
	def __unicode__(self):
		return u'id: ' + unicode(self.id) + ' Amount: ' + unicode(self.amount)
		
class TableNullDate(models.Model):
	amount = models.DateField(null=True)
	
	def __unicode__(self):
		return u'id: ' + unicode(self.id) + ' Amount: ' + unicode(self.amount)
		
class TableNullTime(models.Model):
	amount = models.TimeField(null=True)
	
	def __unicode__(self):
		return u'id: ' + unicode(self.id) + ' Amount: ' + unicode(self.amount)
		
class TableNullBoolean(models.Model):
	amount = models.BooleanField(null=True)
	
	def __unicode__(self):
		return u'id: ' + unicode(self.id) + ' Amount: ' + unicode(self.amount)

class TableNullDecimal(models.Model):
	amount = models.DecimalField(null=True, max_digits=4, decimal_places=2)
	
	def __unicode__(self):
		return u'id: ' + unicode(self.id) + ' Amount: ' + unicode(self.amount)

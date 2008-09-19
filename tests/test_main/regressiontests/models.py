import datetime
import decimal
from django.db import models
from django.test import TestCase

class Bug19Table(models.Model):
    """ A simple model for testing string comparisons.
    
    >>> choices = (
    ...     "no_slashes", "no_slashes_2",
    ...     r"C:\some_folder\somefile.ext", r"\some_folder",
    ...     "some_folder"+'\',
    ...     "[brackets]",
    ...     )
    >>> for c in choices:
    ...     Bug19Table.objects.create(choice=c).save()
    >>> len(Bug19Table.objects.all())
    6    
    >>> len(Bug19Table.objects.filter(choice__contains="shes"))
    2
    >>> len(Bug19Table.objects.filter(choice__endswith="shes"))
    1
    >>> len(Bug19Table.objects.filter(choice__contains=r"der\som"))
    1
    >>> len(Bug19Table.objects.filter(choice__endswith=r"der\somefile.ext"))
    1
    >>> len(Bug19Table.objects.filter(choice__contains="["))
    1
    """
    choice = models.TextField(max_length=200)
    
    def __unicode__(self):
        return self.choice


class Bug21Table(models.Model):
    """
    Test adding decimals as actual types or as strings.
    
    >>> Bug21Table(a='decimal as decimal', d=decimal.Decimal('12.34')).save()
    >>> Bug21Table(a='decimal as string', d=u'56.78').save()
    >>> len(list(Bug21Table.objects.all()))
    2
    """
    a = models.CharField(max_length=50)
    d = models.DecimalField(max_digits=5, decimal_places=2)

class Bug27Table(models.Model):
    """
    Test that extra/select works, and doesn't interfere with the 
    limit/offset implementation.
    
    >>> Bug27Table(a=100).save()
    >>> Bug27Table(a=101).save()
    >>> len(list(Bug27Table.objects.all()))
    2
    
    >>> objs = list(Bug27Table.objects.extra(select={'alias_for_a':'a'}).order_by('a'))
    >>> objs[0].alias_for_a
    100

    >>> objs[1].alias_for_a
    101
    """
    
    a = models.IntegerField()

class Bug23Table(models.Model):
    """
    Test inserting mixed NULL and non-NULL values.

    >>> Bug23Table(mycharfield1=None, mycharfield2="text2", myintfield=1).save()
    >>> Bug23Table(mycharfield1="text1", mycharfield2=None, myintfield=1).save()
    >>> Bug23Table(mycharfield1="text1", mycharfield2="text2", myintfield=None).save()
    >>> Bug23Table(mycharfield1=None, mycharfield2=None, myintfield=1).save()
    >>> Bug23Table(mycharfield1=None, mycharfield2="text2", myintfield=None).save()
    >>> Bug23Table(mycharfield1="text1", mycharfield2=None, myintfield=None).save()
    >>> Bug23Table(mycharfield1=None, mycharfield2=None, myintfield=None).save()
    >>> objs = list(Bug23Table.objects.all())
    >>> len(objs)
    7
    >>> len([obj for obj in objs if obj.mycharfield1=="text1"])
    3
    >>> len([obj for obj in objs if obj.mycharfield2=="text2"])
    3
    >>> len([obj for obj in objs if obj.myintfield==1])
    3
    """
    mycharfield1 = models.CharField(max_length=100, null=True)
    mycharfield2 = models.CharField(max_length=50, null=True)
    myintfield = models.IntegerField(null=True)


# Bug 26 tables, RelatedA and RelatedB
class RelatedB(models.Model):
    a = models.CharField(max_length=50)
    b = models.CharField(max_length=50)
    c = models.CharField(max_length=50)

class RelatedA(models.Model):
    a = models.CharField(max_length=50)
    b = models.ForeignKey(RelatedB)

class Bug26TestCase(TestCase):
    """Test that slicing queries w/ duplicate column names works."""

    def testWithDuplicateColumnNames(self):
        b = RelatedB(a='this is a value', b="valueb", c="valuec")
        b.save()
        
        RelatedA(a="valuea", b=b).save()
        RelatedA(a="valuea", b=b).save()

        items = RelatedA.objects.select_related()[1:2]
        self.assertEqual(len(items), 1)
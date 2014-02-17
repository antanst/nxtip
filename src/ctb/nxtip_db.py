from peewee import *
from nxtip_settings import *

DB = MySQLDatabase(NXTIP_DB, user=NXTIP_DB_USER, passwd=NXTIP_DB_PASS, host=NXTIP_DB_HOST)
DB.connect()

class User(Model):
    name = CharField(null=False)
    key = CharField(null=False)
    account = CharField(null=False)
    balance = FloatField(null=False)

    class Meta:
        database = DB

class Deposit(Model):
    user = ForeignKeyField(User,related_name='deposits',null=False)
    amount = FloatField(null=False) #deposit amount (with TXFEE)
    timestamp = IntegerField(null=False)
    verified = BooleanField(null=False,default=False)
    transaction_id = CharField(null=False)

    class Meta:
        database = DB

class Withdrawal(Model):
    user = ForeignKeyField(User,related_name='withdrawals',null=False)
    amount = FloatField(null=False) #withdrawal amount (with TXFEE)
    timestamp = IntegerField(null=True) #withdrawal transaction's timestam
    verified = BooleanField(null=False,default=False)
    transaction_id = CharField(null=True) #withdrawal transaction's id
    balance = FloatField(null=False) #the balance after the withdrawal

    class Meta:
        database = DB

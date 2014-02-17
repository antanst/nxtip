import json,requests,random,re,time,logging
from nxtip_db import User,Withdrawal,DB
from nxtip_settings import *

class NXTd(object):

    def __init__(self,config=None,rpcserver=None):
        #Altcointip arguments config & rpcserver are ignored
        self.logger=logging.getLogger('cointipbot')

    def nrs_command(self,request_type,params={}):
        """Send command to nxt daemon and return data"""
        params.update({"requestType":request_type})
        while True: #try to connect indefinitely
            try:
                conn=requests.get(NRS_URL,params=params)
                break
            except requests.ConnectionError:
                self.logger.error("Error connecting to NRS daemon.")
            time.sleep(1)
        try:
            data=conn.content
        except KeyError:
            self.logger.error("Unrecognized response from NRS daemon. Params: %s"%params)
            return None
        try:
            result=json.loads(data)
        except ValueError:
            self.logger.error("Cannot parse response from NRS daemon. Params: %s"%params)
            return None
        return result

    def _new_key_account(self):
        """
        Creates a new key/account pair and returns it.
        Does not touch the database.
        """
        #create a new user account. Make sure the account does not exist
        #see here for more info:
        #http://wiki.nxtcrypto.org/wiki/Creating_Nxt_accounts_for_site_users
        while True:
            key=''.join([chr(random.choice(range(33,127))) for i in range(64)])
            account=self.nrs_command("getAccountId",{"secretPhrase":key})["accountId"]
            if self.nrs_command("getAccountPublicKey",{"account":account})=={u'errorCode': 5, u'errorDescription': u'Unknown account'}:
                break
            time.sleep(0.5)
        return {"key":key,"account":account}

    def _getbalance(self,user):
        user=User.select().where(User.name==user).get() #self.couch.get("user_%s"%user)["account"]
        balance=user.balance #self.nrs_command({"requestType":"getBalance","account":account})[conf_type]
        return balance
        
    def getbalance(self,*args): #2nd arg is minconf, ignored
        if args:
            _user=args[0]
        else:
            _user=NXTIP_USER
        return self._getbalance(_user)

    def move(self,*args):
        user_from=User.select().where(User.name==args[0]).get()
        user_to=User.select().where(User.name==args[1]).get()
        amount=args[2]
        if user_from.balance<amount:
            return False
        with DB.transaction():
            user_from.balance-=amount
            user_to.balance+=amount
            user_from.save()
            user_to.save()
        return True

    def sendfrom(self,username_from,account_to,amount,minconf):
        user_from=User.select().where(User.name==username_from).get()
        #round amount to nearest integer,
        #fractional NXT's are not supported yet.
        amount=round(amount)
        #check if the user's balance has enough NXT's
        if user_from.balance<(amount+TXFEE):
            return False
        #ok, withdrawal time! Add the withdrawal.
        #the TXFEE is included in the withdrawal
        #amount, because it is also subtracted
        #from the user's tipping balance.
        withdrawal=Withdrawal.create(user=user_from,
                                     amount=amount+TXFEE,
                                     verified=False,
                                     balance=float(user_from.balance-(amount+TXFEE)))
        #move the funds from the NXT account
        #to the user's NXT account, and
        #remove the amount+TXFEE from the
        #user's tipping balance:
        temp=self.nrs_command("sendMoney",{
            "secretPhrase":NXTIP_KEY,
            "recipient":account_to,
            "amount":int(amount),
            "fee":TXFEE,
            # "referencedTransaction":transaction_id,
            "deadline":"1440" #one day                                                                             
        })
        if "errorCode" in temp:
            self.logger.error("Withdrawal error for user %s: %s"%(user_from.name,temp))
            return False
        transaction=self.nrs_command("getTransaction",{"transaction":temp["transaction"]})
        with DB.transaction():
                withdrawal.timestamp=transaction["timestamp"]
                withdrawal.transaction_id=temp["transaction"]
                withdrawal.verified=True
                user_from.balance-=amount+TXFEE
                user_from.save()
                withdrawal.save()
        return True

    def getnewaddress(self,username):
        if username==NXTIP_USER:
            try:
                user=User.select().where(User.name==NXTIP_USER).get()
            except User.DoesNotExist:
                account={"key":NXTIP_KEY,"account":NXTIP_ACCOUNT}
                user=User.create(name=NXTIP_USER,key=account["key"],account=account["account"],balance=0)
            return NXTIP_ACCOUNT
        try:
            user=User.select().where(User.name==username).get()
        except User.DoesNotExist:
            account=self._new_key_account() #{"key":"..","account":".."}
            user=User.create(name=username,key=account["key"],account=account["account"],balance=0)
        return user.account

    def validateaddress(self,account):
        if re.match("^\d{1,20}$",account):
            return {"isvalid":True}
        else:
            return {"isvalid":False}

    def settxfee(self,ignored):
        pass
    def walletpassphrase(self,ignored1,ignored2):
        pass
    def walletlock(self):
        pass

class Bitcoind(NXTd):
    """For emulating the bitcoin daemon,
    as far as altcointip is concerned"""
    pass


#!/usr/bin/env python
"""
This file checks the NXT user accounts for
deposited NXT's, and moves them to the
nxtip bot's NXT account to be used for
tippings.
"""

from nxtip_settings import *

from nxtip_db import User,Deposit, DB
from nxtd import NXTd
import time

nxtd=NXTd()

def verify_deposits():
    """
    For each deposit that isn't verified,
    check if it's transaction has at least
    2 confirmations and mark is as such.
    """
    unverified_deposits=Deposit.select().where(Deposit.verified==False)
    print("%d deposits to verify"%unverified_deposits.count())
    for deposit in unverified_deposits:
        print("Checking transaction %s"%deposit.transaction_id)
        transaction=nxtd.nrs_command("getTransaction",{"transaction":deposit.transaction_id})
        if "confirmations" in transaction and transaction["confirmations"]>=NXTIP_DEPOSIT_MINCONF:
            with DB.transaction():
                deposit.verified=True
                deposit.user.balance+=deposit.amount
                deposit.user.save()
                deposit.save()
                print("Verified!")
        else:
            print("Not enough confirmations, ignoring for now.")

def make_deposits():
    """
    Check the balances of all
    users' NXT accounts, to find
    which users have made a deposit
    for the bot. The funds are moved
    to the nxtip bot's account.
    """
    users=User.select()
    if not users.count():
        print("No users in database.")
        return
    print("%d users to check for deposits"%users.count())
    for user in users:
        if user.name == NXTIP_USER:
            continue
        print("Checking transactions of user %s, account %s"%(user.name,user.account))
        time.sleep(0.1)
        #Check account transactions that were
        #created later than the last check date.
        #For each incoming transaction (recipient = account)
        #that has at least USER_DEPOSIT_MINCONF confirmations and
        #a deadline of at least 1440 (one day),
        #check if we have deposited this amount.
        #If not, then begin transfer of deposited
        #amount to the nxtip account.
        balance=float(nxtd.nrs_command("getGuaranteedBalance",{"account":user.account,"numberOfConfirmations":USER_DEPOSIT_MINCONF-1})["guaranteedBalance"])/100
        try:
            last_db_timestamp = ((Deposit.select().where(Deposit.user == user).order_by(Deposit.timestamp.desc())).get().timestamp)+1
        except Deposit.DoesNotExist:
            last_db_timestamp=0
        transaction_ids=nxtd.nrs_command("getAccountTransactionIds",{"account":user.account,"timestamp":last_db_timestamp})
        #if the account does not exist, then the user
        #hasn't made any deposits yet.
        if transaction_ids=={u'errorCode': 5, u'errorDescription': u'Unknown account'}:
            continue
        for transaction_id in transaction_ids["transactionIds"]:
            transaction=nxtd.nrs_command("getTransaction",{"transaction":transaction_id})
            print("Checking transaction %s"%transaction_id)
            #only accept transaction if the transaction
            #is incoming, with confirmations >= USER_DEPOSIT_MINCONF
            #and deadline >= 1440
            if transaction["recipient"]==user.account and transaction["confirmations"]>=USER_DEPOSIT_MINCONF and transaction["deadline"]>=1440:
                print("Found deposit transaction %s user %s amount %s confirmations %s"%(transaction_id,
                                                                                         user.name,
                                                                                         transaction["amount"],
                                                                                         transaction["confirmations"]))
                #check if there is a pending deposit already
                #with this transaction
                deposits=Deposit.select().where(Deposit.transaction_id==transaction_id)
                if deposits.count():
                    print("Transaction is already recorded in a deposit and waiting verification")
                    continue
                #Make another check just in case
                if balance<transaction["amount"]:
                    print("User's guaranteed NXT balance is lower than incoming transactions! This shouldn't happen.")
                    break
                #ok, deposit time! Mark the pending deposit:
                deposit=Deposit.create(user=user,
                                       amount=transaction["amount"]-TXFEE,
                                       timestamp=transaction["timestamp"],
                                       transaction_id=transaction_id,
                                       verified=False)
                #move the funds to the NXT account:
                temp=nxtd.nrs_command("sendMoney",{
                    "secretPhrase":user.key,
                    "recipient":NXTIP_ACCOUNT,
                    "amount":transaction["amount"]-TXFEE,
                    "fee":TXFEE,
                    "referencedTransaction":transaction_id,
                    "deadline":"1440" #one day                                                                             
                })
                #record the transaction:
                deposit.transaction_id=temp["transaction"]
                deposit.save()
                #We're finished for now. The transaction
                #has been sent, and when the transaction
                #reaches NXT_DEPOSIT_MINCONF confirmations we'll change
                #the user's tipping balance.
                print("Added unverified deposit and moved funds to tipping bot's account.")
            else:
                print("Found deposit transaction %s user %s amount %s confirmations %s"%(transaction_id,
                                                                                         user.name,
                                                                                         transaction["amount"],
                                                                                         transaction["confirmations"]))
                # reasons=[]
                # if not transaction["recipient"]==user.account:
                #     reasons.append("Not incoming")
                # if not transaction["confirmations"]>=USER_DEPOSIT_MINCONF:
                #     reasons.append("Not enough confirmations")
                # if not transaction["deadline"]>=1440:
                #     reasons.append("Too small deadline")
                # print("Ignoring transaction. Reason: %s"%','.join(reasons))

if __name__=="__main__":
    while True:
        print("-"*80)
        verify_deposits()
        make_deposits()
        delay=30
        print("Finished. Sleeping %d seconds"%delay)
        time.sleep(delay)

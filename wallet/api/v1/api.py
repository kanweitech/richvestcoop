from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.views import APIView
from wallet.models import Action

class UserTransactionRecordAPI(APIView):
    """
    This endpoint returns the User balance and Last 25 transaction records
    """

    permission_classes = [permissions.IsAuthenticated]


    def get(self, request, *args, **kwargs):
        user = self.request.user

        #
        transactions = Action.objects.filter(user=user, wallet=user.wallets)[:25][
            ::-1
        ]
        transaction_list = []
        for transaction in transactions:
            unique_transaction = {}
            unique_transaction["uidref"] = transaction.uidref
            unique_transaction["type"] = transaction.ttype
            unique_transaction["amount"] = transaction.delta
            unique_transaction["metaInfo"] = transaction.meta_info
            unique_transaction["timestamp"] = transaction.timestamp

            transaction_list.append(unique_transaction)

        data = {
            "avail_balance": user.wallets.balance,
            "currency": "NGN",
            "all_transactions": transaction_list,
        }

        return Response({"data": data}, status=status.HTTP_200_OK)


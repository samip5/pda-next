from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models.account import Account
from .serializers import AccountSerializer

class AccountViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for fetching Accounts.

    Provides endpoints to list and retrieve Accounts from the database.
    """
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned records by filtering against
        query parameters in the URL.
        """
        queryset = Account.objects.all()

        # Filter by record name
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset.order_by('name')


    @action(detail=False, methods=['get', 'post'], url_path='manage')
    def accounts(self, request):
        if request.method == 'GET':
            serializer = AccountSerializer(Account.objects.all(), many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            account_name = request.data.get('name', '')
            account = Account.objects.create(
                name=account_name,
            )
            serializer = AccountSerializer(account)
            return Response(serializer.data)

    @action(detail=False, methods=['get', 'post', 'delete'], url_path='manage/(?P<user_id>[^/]+)')
    def account(self, request, user_id=None):
        if request.method == 'GET':
            account = Account.objects.filter(id=user_id).first()
            serializer = AccountSerializer(account, many=False)
            return Response(serializer.data)

        elif request.method == 'POST':
            account = Account.objects.filter(id=user_id).first()
            if request.data.get('name'):
                account.name = request.data.get('name')
            if request.data.get('description'):
                account.description = request.data.get('description')
            if request.data.get('contact'):
                account.contact = request.data.get('contact')
            if request.data.get('mail'):
                account.mail = request.data.get('mail')

            account.save()
            serializer = AccountSerializer(account)
            return Response(serializer.data)

        elif request.method == 'DELETE':
            account = Account.objects.filter(id=user_id).first()
            account.delete()
            return Response("Account deleted")
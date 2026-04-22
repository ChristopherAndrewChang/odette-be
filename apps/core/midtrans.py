import midtransclient
from django.conf import settings


def get_snap_client():
    return midtransclient.Snap(
        is_production=settings.MIDTRANS_IS_PRODUCTION,
        server_key=settings.MIDTRANS_SERVER_KEY,
    )


def create_payment_link(screen_request):
    snap = get_snap_client()

    transaction_details = {
        'order_id': f'SCREEN-{screen_request.id}-{int(screen_request.created_at.timestamp())}',
        'gross_amount': int(screen_request.donation_amount),
    }

    item_details = [{
        'id': screen_request.request_type,
        'price': int(screen_request.donation_amount),
        'quantity': 1,
        'name': f'{screen_request.get_request_type_display()} — Table {screen_request.session.table.number}',
    }]

    customer_details = {
        'first_name': screen_request.session.customer_name,
    }

    param = {
        'transaction_details': transaction_details,
        'item_details': item_details,
        'customer_details': customer_details,
        'payment_type': 'qris',
        'expiry': {
            'unit': 'hours',
            'duration': 2,
        },
    }

    result = snap.create_transaction(param)
    return result.get('redirect_url')
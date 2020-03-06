import getpass
from datetime import datetime, timedelta

from .client import Client


def main() -> None:
    client = Client()

    username = input('Username: ')
    password = getpass.getpass()
    customer = input('Customer: ')

    with client.login(username, password, customer) as connection:
        day_str = input('Date: ')
        day = datetime.strptime(day_str, '%Y-%m-%d').date()
        blocks = connection.get_time_blocks_of_date(day)
        total_time = sum((x.duration for x in blocks), timedelta(0))
        print('\n'.join(f'{x}' for x in blocks))
        print(f'Total time: {total_time}')

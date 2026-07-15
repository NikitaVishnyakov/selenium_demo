# ========= task 1 ===============
import time

import pytest

nums = [1, 2, 3, 2, 4, 5, 3, 6]

# duplicated = []
#
# for i in nums:
#     nums.sort()
#     if i == nums[i] and i not in duplicated:
#         duplicated.append(i)
#
# print(duplicated)



seen = []
dupl = []

for num in nums:
    if num in seen:
        dupl.append(num)
    else:
        seen.append(num)

print(dupl)

# ========= task2===============


counter = 0

def check():
    global counter
    counter += 1
    return counter == 3

# def wait_until(condition, timeout=10, interval=1):
#     time_counter = 0
#     while time_counter <= timeout:
#         time.sleep(interval)
#         time_counter += interval
#         if condition():
#             return True
#         else:
#             return False
#     return False


def wait_until(condition, timeout=10, interval=1):
    start_time = time.time()

    if time.time() - start_time < timeout:
        try:
            if condition():
                return True
            #time.sleep(interval)
        except Exception():
            print(Exception)


    return False


wait_until(check, timeout=5, interval=1)
# → True

# ========= task 3 ===============

response = {
    "user": {
        "id": 15,
        "name": "John",
        "roles": ["admin", "user"]
    }
}

#Напиши проверки через assert, что:

# id существует.
# id является int.
# name == "John".
# Пользователь имеет роль "admin".

if response is not None:
    assert response["user"]["id"] is not None
    assert isinstance(response["user"]["id"], int)
    assert response["user"]["name"] == "John"
    assert "admin" in response["user"]["roles"]


# ========= task 4 ===============

import pytest

def sum_numbers(a, b):
    return a + b

@pytest.mark.parametrize("a,b, expected", [(1,2,3), (5,5,10), (-1,1,0)])
def test_sum_numbers(a, b, expected):
    assert sum_numbers(a, b) == expected

# ========= task 5 ===============

import requests

admin_token = "admin123"
user_token = "user123"

endpoint = "GET /api/users/1"

# Ожидаемое поведение:
# admin_token → 200
# user_token → 403


@pytest.mark.parametrize("token, expected", [(admin_token, 200), (user_token, 403)])
def test_get_user_info(token, expected):
    response = requests.get(endpoint, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == expected
    if response.status_code == expected:
        assert response.json()['error'] == "forbidden"
        assert response.json() == {"name": "john", "id": 123}

# Report

## Description

Project consists of 4 main components:
- Cassandra cluster
- server
- CLI client
- stress tests

The project uses 3 Cassandra nodes running in separate docker containers that communicate with each other over docker network. 

Server interacting with the database is implemented in tornado framework and provides GET, POST and PUT methods handling. It returns status code depending on the result of the operation:
- 200 OK for successful operations
- 400 Bad Request for invalid input data
- 404 Not Found for non existing resources
- 409 Conflict for reservation conflicts
All responses are in JSON format which contains `error` field with text description of error in case the status code is not 200 and null otherwise. If the operation is successful, the response contains other field with name depending on the operation.

The client provides simple CLI to interact with the server. It allows to view movies, view user reservations, make a new reservation and change user name displayed on reservation. Making a new reservation and changing user name are interactive operations that require user input. 

Stress tests are implemented using `autocannon` library and consist of 3 tests:
1. The client makes the same request very quickly.
2. Three clients make the possible requests randomly.
3. Two clients try to reserve all seats at the same time.

The tests are designed to check the correctness of the application under high load and to measure the latency of operations.

The problem of concurrent writes is solved by delegating it to the database. Lightweight transactions are used to ensure that no seat can be reserved by more than one person. This works because reservations table has both `screening_id` and `seat_number` as primary key which allows only one reservation per seat for a screening.

## Database schema

Database contains 3 tables: `movies`, `reservations` and `reservations_by_user`.

**Movies** \
├ **screening_id**: UUID \
├ movie_title: text \
├ screening_time: timestamp \
├ room_number: int \
└ total_seats: int \
Holds basic information about the movie screenings with most important total seats in the room which defines number of possible reservations.

**Reservations** \
├ **screening_id**: UUID \
├ **seat_number**: int \
├ reservation_id: UUID \
├ screening_time: timestamp \
├ movie_title: text \
├ user_name: text \
└ user_email: text \
Combination of `screening_id` and `seat_number` is used as a primary key to ensure that each seat can be reserved only once for each screening.

**Reservations_by_user** \
├ **user_email**: text \
├ **reservation_id**: UUID \
├ user_name: text \
├ movie_title: text \
├ screening_id: UUID \
├ screening_time: timestamp \
└ seat_number: int \
Uses `user_email` and `reservation_id` as a primary key to allow fetching all reservations for a user without filtering across partitions.

## Problems

The main problem was denormalizing database tables to avoid using filtering across partitions. This was solved by creating `reservations_by_user` table that is used to fetch user reservations.

Other problem was ensuring that these two tables are consistent after update operations, which was solved by using batch statements which are executed atomically by Cassandra.

## Stress test results

The application handles calls with low latency that is not noticeable for the user. None of the tests resulted in server errors, all errors were properly handled by returning 400 Bad Request, 404 Not Found or 409 Conflict status codes depending on the error type.

For read operations the latency is around 20 ms with max peak at 50 ms. For write operations the latency is higher with the average around 60 ms but still the maximum latency does not exceed 200 ms which is not noticeable for the user.

The latencies are higher if we flood the server with requests at the same time but even then it sends responses mostly below 1 second.

In the last test where two clients try to simultaneously reserve all seats for the same screening, the server successfully handles conflicts and allows to reserve only available seats. In the end all seats are reserved and both clients get some of the seats reserved. The split varies between runs because of the indeterminism of the order of requests in which they arrive at the server.

Exact results of the stress tests are shown below:
```
================================================================================
                                     Test 1                                     
================================================================================
Running 30s test @ http://localhost:8888
10 connections


┌─────────┬───────┬───────┬───────┬───────┬──────────┬─────────┬───────┐
│ Stat    │ 2.5%  │ 50%   │ 97.5% │ 99%   │ Avg      │ Stdev   │ Max   │
├─────────┼───────┼───────┼───────┼───────┼──────────┼─────────┼───────┤
│ Latency │ 12 ms │ 16 ms │ 27 ms │ 32 ms │ 16.67 ms │ 3.73 ms │ 56 ms │
└─────────┴───────┴───────┴───────┴───────┴──────────┴─────────┴───────┘
┌───────────┬────────┬────────┬────────┬────────┬────────┬─────────┬────────┐
│ Stat      │ 1%     │ 2.5%   │ 50%    │ 97.5%  │ Avg    │ Stdev   │ Min    │
├───────────┼────────┼────────┼────────┼────────┼────────┼─────────┼────────┤
│ Req/Sec   │ 497    │ 497    │ 575    │ 676    │ 582.4  │ 39.58   │ 497    │
├───────────┼────────┼────────┼────────┼────────┼────────┼─────────┼────────┤
│ Bytes/Sec │ 250 kB │ 250 kB │ 289 kB │ 340 kB │ 293 kB │ 19.9 kB │ 250 kB │
└───────────┴────────┴────────┴────────┴────────┴────────┴─────────┴────────┘

Req/Bytes counts sampled once per second.
# of samples: 30

17k requests in 30.04s, 8.79 MB read

================================================================================
                                     Test 2                                     
================================================================================
Using screening: Inception (53c4fa06-d37a-4a02-b76c-8a346d4ad64c), total seats: 100

Running 30s test @ http://localhost:8888
5 connections


┌─────────┬───────┬───────┬────────┬────────┬──────────┬──────────┬────────┐
│ Stat    │ 2.5%  │ 50%   │ 97.5%  │ 99%    │ Avg      │ Stdev    │ Max    │
├─────────┼───────┼───────┼────────┼────────┼──────────┼──────────┼────────┤
│ Latency │ 35 ms │ 57 ms │ 107 ms │ 130 ms │ 61.33 ms │ 20.76 ms │ 189 ms │
└─────────┴───────┴───────┴────────┴────────┴──────────┴──────────┴────────┘
┌───────────┬────────┬────────┬────────┬────────┬────────┬─────────┬────────┐
│ Stat      │ 1%     │ 2.5%   │ 50%    │ 97.5%  │ Avg    │ Stdev   │ Min    │
├───────────┼────────┼────────┼────────┼────────┼────────┼─────────┼────────┤
│ Req/Sec   │ 70     │ 70     │ 80     │ 91     │ 80.77  │ 5.64    │ 70     │
├───────────┼────────┼────────┼────────┼────────┼────────┼─────────┼────────┤
│ Bytes/Sec │ 136 kB │ 136 kB │ 410 kB │ 608 kB │ 453 kB │ 94.8 kB │ 136 kB │
└───────────┴────────┴────────┴────────┴────────┴────────┴─────────┴────────┘

Req/Bytes counts sampled once per second.
# of samples: 30

1410 2xx responses, 1013 non 2xx responses
2k requests in 30.02s, 13.6 MB read

┌─────────┬───────┬───────┬────────┬────────┬──────────┬──────────┬────────┐
│ Stat    │ 2.5%  │ 50%   │ 97.5%  │ 99%    │ Avg      │ Stdev    │ Max    │
├─────────┼───────┼───────┼────────┼────────┼──────────┼──────────┼────────┤
│ Latency │ 34 ms │ 56 ms │ 107 ms │ 127 ms │ 61.43 ms │ 20.97 ms │ 182 ms │
└─────────┴───────┴───────┴────────┴────────┴──────────┴──────────┴────────┘
┌───────────┬─────────┬─────────┬────────┬────────┬────────┬─────────┬─────────┐
│ Stat      │ 1%      │ 2.5%    │ 50%    │ 97.5%  │ Avg    │ Stdev   │ Min     │
├───────────┼─────────┼─────────┼────────┼────────┼────────┼─────────┼─────────┤
│ Req/Sec   │ 70      │ 70      │ 80     │ 91     │ 80.8   │ 5.27    │ 70      │
├───────────┼─────────┼─────────┼────────┼────────┼────────┼─────────┼─────────┤
│ Bytes/Sec │ 89.7 kB │ 89.7 kB │ 410 kB │ 607 kB │ 454 kB │ 99.8 kB │ 89.7 kB │
└───────────┴─────────┴─────────┴────────┴────────┴────────┴─────────┴─────────┘

Req/Bytes counts sampled once per second.
# of samples: 30

1409 2xx responses, 1015 non 2xx responses
2k requests in 30.06s, 13.6 MB read

┌─────────┬───────┬───────┬────────┬────────┬──────────┬─────────┬────────┐
│ Stat    │ 2.5%  │ 50%   │ 97.5%  │ 99%    │ Avg      │ Stdev   │ Max    │
├─────────┼───────┼───────┼────────┼────────┼──────────┼─────────┼────────┤
│ Latency │ 35 ms │ 57 ms │ 111 ms │ 132 ms │ 61.41 ms │ 21.1 ms │ 190 ms │
└─────────┴───────┴───────┴────────┴────────┴──────────┴─────────┴────────┘
┌───────────┬─────────┬─────────┬────────┬────────┬────────┬────────┬─────────┐
│ Stat      │ 1%      │ 2.5%    │ 50%    │ 97.5%  │ Avg    │ Stdev  │ Min     │
├───────────┼─────────┼─────────┼────────┼────────┼────────┼────────┼─────────┤
│ Req/Sec   │ 68      │ 68      │ 80     │ 92     │ 80.67  │ 6      │ 68      │
├───────────┼─────────┼─────────┼────────┼────────┼────────┼────────┼─────────┤
│ Bytes/Sec │ 89.9 kB │ 89.9 kB │ 410 kB │ 607 kB │ 451 kB │ 102 kB │ 89.8 kB │
└───────────┴─────────┴─────────┴────────┴────────┴────────┴────────┴─────────┘

Req/Bytes counts sampled once per second.
# of samples: 30

1398 2xx responses, 1022 non 2xx responses
2k requests in 30.07s, 13.5 MB read

================================================================================
                                     Test 3                                     
================================================================================
Screening: The Matrix (36427e61-e253-4454-b30b-0e61d17351a9)
Total seats: 80
Running 80 requests test @ http://localhost:8888
80 connections


┌─────────┬────────┬────────┬────────┬────────┬───────────┬──────────┬────────┐
│ Stat    │ 2.5%   │ 50%    │ 97.5%  │ 99%    │ Avg       │ Stdev    │ Max    │
├─────────┼────────┼────────┼────────┼────────┼───────────┼──────────┼────────┤
│ Latency │ 517 ms │ 697 ms │ 925 ms │ 944 ms │ 705.35 ms │ 117.3 ms │ 944 ms │
└─────────┴────────┴────────┴────────┴────────┴───────────┴──────────┴────────┘
┌───────────┬─────────┬─────────┬─────────┬─────────┬─────────┬───────┬─────────┐
│ Stat      │ 1%      │ 2.5%    │ 50%     │ 97.5%   │ Avg     │ Stdev │ Min     │
├───────────┼─────────┼─────────┼─────────┼─────────┼─────────┼───────┼─────────┤
│ Req/Sec   │ 80      │ 80      │ 80      │ 80      │ 80      │ 0     │ 80      │
├───────────┼─────────┼─────────┼─────────┼─────────┼─────────┼───────┼─────────┤
│ Bytes/Sec │ 13.2 kB │ 13.2 kB │ 13.2 kB │ 13.2 kB │ 13.2 kB │ 0 B   │ 13.2 kB │
└───────────┴─────────┴─────────┴─────────┴─────────┴─────────┴───────┴─────────┘

Req/Bytes counts sampled once per second.
# of samples: 1

32 2xx responses, 48 non 2xx responses
80 requests in 1.07s, 13.2 kB read

┌─────────┬────────┬────────┬─────────┬─────────┬───────────┬───────────┬─────────┐
│ Stat    │ 2.5%   │ 50%    │ 97.5%   │ 99%     │ Avg       │ Stdev     │ Max     │
├─────────┼────────┼────────┼─────────┼─────────┼───────────┼───────────┼─────────┤
│ Latency │ 133 ms │ 351 ms │ 1236 ms │ 1255 ms │ 607.07 ms │ 417.96 ms │ 1255 ms │
└─────────┴────────┴────────┴─────────┴─────────┴───────────┴───────────┴─────────┘
┌───────────┬─────────┬─────────┬─────────┬─────────┬─────────┬─────────┬─────────┐
│ Stat      │ 1%      │ 2.5%    │ 50%     │ 97.5%   │ Avg     │ Stdev   │ Min     │
├───────────┼─────────┼─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
│ Req/Sec   │ 21      │ 21      │ 21      │ 59      │ 40      │ 19      │ 21      │
├───────────┼─────────┼─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
│ Bytes/Sec │ 3.65 kB │ 3.65 kB │ 3.65 kB │ 9.21 kB │ 6.43 kB │ 2.78 kB │ 3.65 kB │
└───────────┴─────────┴─────────┴─────────┴─────────┴─────────┴─────────┴─────────┘

Req/Bytes counts sampled once per second.
# of samples: 2

48 2xx responses, 32 non 2xx responses
80 requests in 2.07s, 12.9 kB read
Total seats booked: 80 / 80
  User A: 32 seat(s)
  User B: 48 seat(s)
```
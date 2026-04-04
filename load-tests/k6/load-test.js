import http from 'k6/http';
import { check, sleep } from 'k6';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.2/index.js';

export const options = {
  stages: [
    { duration: '30s', target: 5 },
    { duration: '1m', target: 20 },
    { duration: '1m', target: 50 },
    { duration: '30s', target: 100 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.05'],
    http_req_duration: ['p(95)<1000'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://dispatcher:8000';

function login(username, password) {
  const payload = JSON.stringify({ username, password });
  const params = {
    headers: { 'Content-Type': 'application/json' },
  };

  const res = http.post(`${BASE_URL}/auth/login`, payload, params);

  check(res, {
    'login status is 200': (r) => r.status === 200,
  });

  if (res.status !== 200) return null;
  return res.json('access_token');
}

export default function () {
  const isAdmin = (__VU % 10) === 0;
  const username = isAdmin ? 'admin' : 'user';
  const token = login(username, '1234');

  if (!token) {
    sleep(1);
    return;
  }

  const authParams = {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  };

  let res = http.get(`${BASE_URL}/products`, authParams);
  check(res, {
    'products status is 200': (r) => r.status === 200,
  });

  res = http.post(
    `${BASE_URL}/orders`,
    JSON.stringify({
      product_id: 1,
      quantity: 1 + (__ITER % 3),
    }),
    authParams
  );
  check(res, {
    'order status is 201': (r) => r.status === 201,
  });

  if (isAdmin && __ITER % 5 === 0) {
    res = http.post(
      `${BASE_URL}/products`,
      JSON.stringify({
        name: `K6 Product ${__VU}-${__ITER}`,
        price: 999,
      }),
      authParams
    );

    check(res, {
      'admin product create status is 201': (r) => r.status === 201,
    });
  }

  sleep(1);
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    '/scripts/results/summary.json': JSON.stringify(data, null, 2),
  };
}
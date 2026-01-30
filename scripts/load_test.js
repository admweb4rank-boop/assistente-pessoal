/**
 * Load Testing Configuration for k6
 * Run with: k6 run scripts/load_test.js
 */

// ============================================================================
// Configuration
// ============================================================================

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const taskCreationTime = new Trend('task_creation_time');
const inboxProcessingTime = new Trend('inbox_processing_time');
const healthCheckTime = new Trend('health_check_time');
const successfulRequests = new Counter('successful_requests');

// Test configuration
export const options = {
  // Stages for ramping up/down
  stages: [
    { duration: '30s', target: 10 },   // Ramp up to 10 users
    { duration: '1m', target: 10 },    // Stay at 10 users
    { duration: '30s', target: 25 },   // Ramp up to 25 users
    { duration: '2m', target: 25 },    // Stay at 25 users
    { duration: '30s', target: 50 },   // Ramp up to 50 users
    { duration: '2m', target: 50 },    // Stay at 50 users
    { duration: '30s', target: 0 },    // Ramp down to 0
  ],
  
  // Thresholds for pass/fail
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],  // 95% under 500ms, 99% under 1s
    http_req_failed: ['rate<0.01'],                  // Error rate under 1%
    errors: ['rate<0.05'],                           // Custom error rate under 5%
    health_check_time: ['p(95)<100'],                // Health checks under 100ms
    task_creation_time: ['p(95)<300'],               // Task creation under 300ms
  },
  
  // Tags for grouping
  tags: {
    testType: 'load',
    service: 'igor-backend'
  }
};

// ============================================================================
// Test Configuration
// ============================================================================

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8090';
const API_KEY = __ENV.API_KEY || 'tb-personal-os-2026-igor-secret-key-change-in-production';

const headers = {
  'Content-Type': 'application/json',
  'X-API-Key': API_KEY
};

// ============================================================================
// Test Scenarios
// ============================================================================

export default function () {
  // Health Check
  group('Health Check', function () {
    const start = Date.now();
    const res = http.get(`${BASE_URL}/health`);
    healthCheckTime.add(Date.now() - start);
    
    const success = check(res, {
      'health check status is 200': (r) => r.status === 200,
      'health check response has status': (r) => JSON.parse(r.body).status !== undefined,
    });
    
    errorRate.add(!success);
    if (success) successfulRequests.add(1);
  });
  
  sleep(0.5);
  
  // List Tasks
  group('List Tasks', function () {
    const res = http.get(`${BASE_URL}/api/v1/tasks`, { headers });
    
    const success = check(res, {
      'list tasks status is 200': (r) => r.status === 200,
      'list tasks returns array': (r) => Array.isArray(JSON.parse(r.body)),
    });
    
    errorRate.add(!success);
    if (success) successfulRequests.add(1);
  });
  
  sleep(0.5);
  
  // Create Task
  group('Create Task', function () {
    const start = Date.now();
    const payload = JSON.stringify({
      title: `Load Test Task ${Date.now()}`,
      description: 'Created during load test',
      priority: 'medium'
    });
    
    const res = http.post(`${BASE_URL}/api/v1/tasks`, payload, { headers });
    taskCreationTime.add(Date.now() - start);
    
    const success = check(res, {
      'create task status is 200 or 201': (r) => r.status === 200 || r.status === 201,
      'create task returns id': (r) => {
        try {
          return JSON.parse(r.body).id !== undefined;
        } catch {
          return false;
        }
      },
    });
    
    errorRate.add(!success);
    if (success) successfulRequests.add(1);
  });
  
  sleep(0.5);
  
  // List Inbox
  group('List Inbox', function () {
    const res = http.get(`${BASE_URL}/api/v1/inbox`, { headers });
    
    const success = check(res, {
      'list inbox status is 200': (r) => r.status === 200,
    });
    
    errorRate.add(!success);
    if (success) successfulRequests.add(1);
  });
  
  sleep(0.5);
  
  // Create Inbox Item
  group('Create Inbox Item', function () {
    const start = Date.now();
    const payload = JSON.stringify({
      content: `Load test message ${Date.now()}`,
      source: 'api'
    });
    
    const res = http.post(`${BASE_URL}/api/v1/inbox`, payload, { headers });
    inboxProcessingTime.add(Date.now() - start);
    
    const success = check(res, {
      'create inbox status is 200 or 201': (r) => r.status === 200 || r.status === 201,
    });
    
    errorRate.add(!success);
    if (success) successfulRequests.add(1);
  });
  
  sleep(0.5);
  
  // List Projects
  group('List Projects', function () {
    const res = http.get(`${BASE_URL}/api/v1/projects`, { headers });
    
    const success = check(res, {
      'list projects status is 200': (r) => r.status === 200,
    });
    
    errorRate.add(!success);
    if (success) successfulRequests.add(1);
  });
  
  sleep(0.5);
  
  // Get Insights Dashboard
  group('Insights Dashboard', function () {
    const res = http.get(`${BASE_URL}/api/v1/insights/dashboard`, { headers });
    
    const success = check(res, {
      'insights dashboard status is 200': (r) => r.status === 200,
    });
    
    errorRate.add(!success);
    if (success) successfulRequests.add(1);
  });
  
  sleep(0.5);
  
  // Health Detailed
  group('Health Detailed', function () {
    const res = http.get(`${BASE_URL}/health/detailed`, { headers });
    
    const success = check(res, {
      'health detailed status is 200': (r) => r.status === 200,
      'health detailed has components': (r) => {
        try {
          return JSON.parse(r.body).components !== undefined;
        } catch {
          return false;
        }
      },
    });
    
    errorRate.add(!success);
    if (success) successfulRequests.add(1);
  });
  
  sleep(1);
}

// ============================================================================
// Stress Test Scenario
// ============================================================================

export function stressTest() {
  // Rapid-fire health checks
  for (let i = 0; i < 10; i++) {
    http.get(`${BASE_URL}/health`);
  }
  
  sleep(0.1);
}

// ============================================================================
// Spike Test Scenario
// ============================================================================

export const spikeTestOptions = {
  stages: [
    { duration: '10s', target: 10 },   // Normal load
    { duration: '1s', target: 100 },   // Spike to 100 users
    { duration: '30s', target: 100 },  // Stay at spike
    { duration: '1s', target: 10 },    // Back to normal
    { duration: '20s', target: 10 },   // Recovery
    { duration: '10s', target: 0 },    // Ramp down
  ],
};

// ============================================================================
// Soak Test Scenario (Long-running)
// ============================================================================

export const soakTestOptions = {
  stages: [
    { duration: '2m', target: 20 },    // Ramp up
    { duration: '30m', target: 20 },   // Stay at 20 for 30 min
    { duration: '2m', target: 0 },     // Ramp down
  ],
};

// ============================================================================
// Teardown
// ============================================================================

export function teardown(data) {
  console.log('Load test completed');
  console.log(`Total successful requests: ${successfulRequests}`);
}

// ============================================================================
// Summary
// ============================================================================

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'summary.json': JSON.stringify(data, null, 2),
  };
}

function textSummary(data, options) {
  // Simple text summary
  const metrics = data.metrics;
  let summary = '\n========== LOAD TEST SUMMARY ==========\n\n';
  
  summary += `Total Requests: ${metrics.http_reqs?.values?.count || 0}\n`;
  summary += `Failed Requests: ${metrics.http_req_failed?.values?.passes || 0}\n`;
  summary += `Avg Response Time: ${(metrics.http_req_duration?.values?.avg || 0).toFixed(2)}ms\n`;
  summary += `P95 Response Time: ${(metrics.http_req_duration?.values['p(95)'] || 0).toFixed(2)}ms\n`;
  summary += `P99 Response Time: ${(metrics.http_req_duration?.values['p(99)'] || 0).toFixed(2)}ms\n`;
  summary += `Error Rate: ${((metrics.errors?.values?.rate || 0) * 100).toFixed(2)}%\n`;
  
  summary += '\n========================================\n';
  
  return summary;
}

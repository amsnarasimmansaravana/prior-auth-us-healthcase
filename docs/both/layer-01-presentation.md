# Layer 1: Presentation Layer
## Channel Services - Healthcare Insurance PA Platform

**Layer Purpose**: User interface and multi-channel intake for PA requests  
**Services**: 6 channel services  
**Technology Stack**: React, Node.js, FastAPI, Azure Speech, Azure Form Recognizer  
**Daily Volume**: 50,000 PA requests across 5 channels  
**Uptime SLA**: 99.95%

---

## Table of Contents
1. [Layer Overview](#layer-overview)
2. [Service Architecture](#service-architecture)
3. [Technical Implementation](#technical-implementation)
4. [API Specifications](#api-specifications)
5. [Data Flow](#data-flow)
6. [Security & Compliance](#security--compliance)
7. [Performance & Scaling](#performance--scaling)
8. [Monitoring & Operations](#monitoring--operations)

---

## Layer Overview

### Purpose
The Presentation Layer serves as the **entry point** for all Prior Authorization requests into the platform. It provides:
- **Multi-channel intake**: Web, Mobile, EDI, Fax, IVR
- **User experience**: React-based UIs for providers and members
- **Document processing**: OCR and fax handling
- **Real-time status**: WebSocket updates for PA status
- **Accessibility**: WCAG 2.1 AA compliance

### Architecture Principles
- **Channel Independence**: Each channel operates independently
- **API-First Design**: All channels use standardized REST/gRPC APIs
- **Stateless Services**: No session affinity required
- **Horizontal Scaling**: Auto-scale based on traffic
- **Fault Isolation**: Channel failures don't cascade

---

## Service Architecture

### Service Inventory (6 Services)

#### 1. **Web Portal Service** (`web-portal-svc`)
**Technology**: React 18.2, TypeScript 5.1, Node.js 20 LTS, Next.js 14  
**Purpose**: Member and provider web portal  
**Port**: 3000  
**Deployment**: Azure Kubernetes Service (AKS), 5-15 replicas

**Features**:
- PA request submission with document upload
- Real-time case status tracking
- Notification center (bell icon with unread count)
- Provider NPI lookup with autocomplete
- Member enrollment verification
- Multi-step form wizard (6 steps)
- Responsive design (mobile, tablet, desktop)

**Tech Stack Details**:
```yaml
Frontend:
  Framework: React 18.2 + Next.js 14 (App Router)
  Language: TypeScript 5.1
  State Management: Zustand 4.3
  UI Library: Material-UI (MUI) 5.14
  Forms: React Hook Form 7.45 + Zod validation
  HTTP Client: Axios 1.4
  WebSocket: Socket.io-client 4.6

Backend (BFF - Backend for Frontend):
  Runtime: Node.js 20 LTS
  Framework: Express.js 4.18
  API Gateway Integration: Kong Admin API
  Session Store: Redis (connect-redis)
  Authentication: Passport.js (OAuth2, SAML)
```

**Key Endpoints**:
```
GET  /                         - Home page
GET  /submit-pa               - PA submission form
POST /api/v1/pa/submit        - Submit PA request
GET  /api/v1/pa/:id           - Get PA details
GET  /api/v1/pa/:id/status    - Real-time status updates
POST /api/v1/documents/upload - Upload supporting documents
GET  /api/v1/notifications    - Get user notifications
```

**Performance**:
- **Page Load Time**: <2 seconds (P95)
- **Form Submit**: <500ms (P95)
- **Document Upload**: Chunked upload for files >10MB
- **Bundle Size**: 185 KB gzipped
- **Lighthouse Score**: 95+ (Performance, Accessibility)

---

#### 2. **Mobile API Service** (`mobile-api-svc`)
**Technology**: FastAPI 0.104, Python 3.11, Pydantic 2.4  
**Purpose**: Native mobile app backend  
**Port**: 8001  
**Deployment**: AKS, 3-8 replicas

**Features**:
- RESTful API for iOS and Android apps
- JWT authentication with refresh tokens
- Push notification registration (FCM, APNS)
- Offline mode support (data sync)
- Image compression and upload
- Location-based provider search
- Biometric authentication support

**Tech Stack Details**:
```yaml
Framework: FastAPI 0.104 (async Python)
Language: Python 3.11
Validation: Pydantic 2.4
Database: PostgreSQL 15 (asyncpg driver)
Cache: Redis (aioredis)
Authentication: JWT (PyJWT) + OAuth2
Push Notifications: 
  - Firebase Cloud Messaging (FCM)
  - Apple Push Notification Service (APNS)
Image Processing: Pillow 10.0
```

**API Endpoints**:
```python
# Authentication
POST   /api/mobile/v1/auth/login          - Login with credentials
POST   /api/mobile/v1/auth/refresh        - Refresh JWT token
POST   /api/mobile/v1/auth/logout         - Logout

# PA Operations
POST   /api/mobile/v1/pa/submit           - Submit PA request
GET    /api/mobile/v1/pa/list             - List user's PAs
GET    /api/mobile/v1/pa/{id}             - Get PA details
PATCH  /api/mobile/v1/pa/{id}/cancel      - Cancel PA

# Documents
POST   /api/mobile/v1/documents/upload    - Upload document (multipart)
GET    /api/mobile/v1/documents/{id}      - Download document

# Notifications
POST   /api/mobile/v1/push/register       - Register device for push
GET    /api/mobile/v1/notifications       - Get notifications
PATCH  /api/mobile/v1/notifications/{id}  - Mark as read
```

**Request/Response Example**:
```json
// POST /api/mobile/v1/pa/submit
{
  "member_id": "M-987654321",
  "provider_npi": "1234567890",
  "procedure_code": "72148",
  "diagnosis_codes": ["M54.5", "M51.16"],
  "urgency": "standard",
  "documents": ["doc-uuid-1", "doc-uuid-2"]
}

// Response
{
  "case_id": "PA-2026-123456",
  "status": "submitted",
  "submission_date": "2026-06-02T10:30:00Z",
  "estimated_decision": "2026-06-02T11:00:00Z"
}
```

**Performance**:
- **API Latency**: <100ms (P95)
- **Throughput**: 5,000 requests/second
- **Concurrent Connections**: 10,000+

---

#### 3. **Provider Portal Service** (`provider-portal-svc`)
**Technology**: Angular 16, TypeScript 5.1, RxJS 7.8  
**Purpose**: Provider office PA management  
**Port**: 3001  
**Deployment**: AKS, 3-10 replicas

**Features**:
- Bulk PA submission (CSV upload)
- Patient lookup and verification
- PA history and analytics dashboard
- Fax integration for decision letters
- Authorization tracking calendar
- EHR integration hooks (Epic, Cerner)

**Tech Stack Details**:
```yaml
Frontend:
  Framework: Angular 16
  Language: TypeScript 5.1
  State Management: NgRx 16 (Redux pattern)
  UI Library: PrimeNG 16
  HTTP: HttpClient (Angular)
  Reactive Programming: RxJS 7.8

Backend (BFF):
  Runtime: Node.js 20 LTS
  Framework: NestJS 10.2
  ORM: Prisma 5.3
  Validation: class-validator
```

**Key Features**:
```typescript
// Bulk PA Submission
interface BulkPASubmission {
  provider_npi: string;
  patients: Array<{
    member_id: string;
    procedure_code: string;
    diagnosis_codes: string[];
    clinical_notes: string;
  }>;
}

// POST /api/provider/v1/pa/bulk-submit
// Response: { job_id: string, total: number, status: "processing" }

// GET /api/provider/v1/pa/bulk-status/{job_id}
// Response: { completed: 45, failed: 2, pending: 3 }
```

**Performance**:
- **Bulk Upload**: 1,000 PAs per CSV
- **Processing**: 50 PAs/second
- **Dashboard Load**: <3 seconds

---

#### 4. **EDI Gateway Service** (`edi-gateway-svc`)
**Technology**: Go 1.21, X12 Parser, HL7 FHIR R4  
**Purpose**: Electronic Data Interchange (X12 278/837)  
**Port**: 8002  
**Deployment**: AKS, 2-5 replicas

**Features**:
- X12 278 (PA Request/Response) processing
- X12 837 (Claims) cross-reference
- HL7 FHIR R4 conversion
- AS2/SFTP/HTTPS transport protocols
- Trading partner management
- Compliance validation (HIPAA 5010)

**Tech Stack Details**:
```yaml
Language: Go 1.21
X12 Library: Custom parser (HIPAA 5010 compliant)
FHIR: HAPI FHIR Go client
Transport:
  - AS2: Drummond certified
  - SFTP: SSH 2.0
  - HTTPS: TLS 1.3
Validation: EDI schema validation engine
Queue: Apache Kafka (async processing)
```

**X12 278 Transaction Flow**:
```
Inbound:
1. Receive X12 278 Request (ISA → GS → ST → UM → SE → GE → IEA)
2. Validate syntax (segment positions, element counts)
3. Validate semantics (NPI, dates, codes)
4. Convert to internal JSON format
5. Submit to workflow engine
6. Return X12 997 (Functional Acknowledgment)

Outbound:
1. Receive decision from workflow
2. Generate X12 278 Response
   - UM03 = Service Review Decision Code
   - Certification number (REF*BB)
   - Valid dates (DTP)
3. Send via AS2/SFTP
```

**Sample X12 278**:
```
ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *260602*1030*^*00501*000000001*0*P*:~
GS*HS*SENDER*RECEIVER*20260602*1030*1*X*005010X217~
ST*278*0001*005010X217~
BHT*0078*13*PA-2026-123456*20260602*1030*RU~
HL*1**20*1~
NM1*PR*2*INSURANCE CO*****PI*12345~
HL*2*1*21*1~
NM1*1P*1*DOE*JANE****XX*1234567890~
HL*3*2*22*0~
NM1*IL*1*SMITH*JOHN****MI*M-987654321~
UM*HS*I*43**C***10~
SV1*HC:72148*500*UN*1~
SE*12*0001~
GE*1*1~
IEA*1*000000001~
```

**Performance**:
- **Throughput**: 2,000 transactions/hour
- **Latency**: <500ms per transaction
- **Error Rate**: <0.1%

---

#### 5. **Fax OCR Service** (`fax-ocr-svc`)
**Technology**: Azure Form Recognizer, Python 3.11, OpenCV  
**Purpose**: Fax intake with OCR  
**Port**: 8003  
**Deployment**: AKS, 2-4 replicas

**Features**:
- Fax-to-email reception (Twilio, RingCentral)
- TIFF/PDF format handling
- Azure Form Recognizer OCR
- Handwriting recognition
- Data extraction (member ID, NPI, codes)
- Quality validation (300+ DPI)
- Document classification

**Tech Stack Details**:
```yaml
Language: Python 3.11
OCR Engine: Azure Form Recognizer (Custom models)
Image Processing: OpenCV 4.8, Pillow 10.0
Fax Integration: 
  - Twilio Fax API
  - RingCentral Fax
PDF Processing: PyPDF2, pdf2image
ML Models: Custom Azure Form Recognizer models
Queue: Azure Queue Storage (async OCR)
```

**Processing Pipeline**:
```python
# Fax Processing Flow
1. Receive fax (Twilio webhook → /fax/receive)
   - Store TIFF in Azure Blob Storage
   - Generate unique fax_id

2. Pre-process image
   - Convert TIFF → PNG (300 DPI)
   - Deskew (OpenCV Hough transform)
   - Denoise (Gaussian blur)
   - Enhance contrast (CLAHE)

3. OCR with Azure Form Recognizer
   - Use custom trained model
   - Extract structured fields:
     * Member ID (confidence threshold: 0.90)
     * Provider NPI (0.95)
     * Procedure codes (0.85)
     * Diagnosis codes (0.85)
     * Clinical notes (0.75)

4. Post-process & validate
   - Luhn check for member ID
   - NPI registry validation
   - CPT/ICD-10 code lookup

5. Human review (if confidence < threshold)
   - Queue to HITL system
   - Display original + extracted data

6. Submit to workflow engine
```

**OCR Accuracy**:
- **Printed Text**: 98.5% accuracy
- **Handwritten**: 92% accuracy
- **Processing Time**: 15-30 seconds per page

---

#### 6. **Voice IVR Service** (`voice-ivr-svc`)
**Technology**: Azure Speech SDK, Node.js 20, Twilio  
**Purpose**: Phone intake and status check  
**Port**: 8004  
**Deployment**: AKS, 2-3 replicas

**Features**:
- Speech-to-Text (Azure Speech Services)
- Text-to-Speech (Natural voices)
- DTMF (touch-tone) input
- PA status lookup by case ID or phone number
- Transfer to human agent (skills-based routing)
- Multi-language support (EN, ES)

**Tech Stack Details**:
```yaml
Language: Node.js 20 (TypeScript)
Speech Services: Azure Cognitive Services Speech SDK
Telephony: Twilio Programmable Voice
NLU: Azure LUIS (intent recognition)
TTS Voices: Azure Neural TTS (en-US-JennyNeural)
Session Store: Redis (call state)
```

**Call Flow**:
```javascript
// Inbound Call Flow
1. Answer call (Twilio webhook)
   → "Thank you for calling PA Health. Press 1 to submit..."

2. Capture DTMF input
   → Option 1: Submit PA
   → Option 2: Check status
   → Option 0: Agent transfer

3. If Submit PA:
   → Collect member ID (STT)
   → Collect provider NPI (STT)
   → Collect procedure code (STT)
   → Confirm details (TTS)
   → Submit to API
   → Provide case ID (TTS)

4. If Check Status:
   → Collect case ID or phone number (STT + DTMF)
   → Lookup in database
   → Read status (TTS)
   → Offer to transfer to agent

5. End call or transfer
```

**IVR Menu Example**:
```xml
<Response>
  <Gather action="/ivr/menu" numDigits="1" timeout="5">
    <Say voice="Polly.Joanna">
      Thank you for calling P A Health. 
      Press 1 to submit a new prior authorization.
      Press 2 to check the status of an existing request.
      Press 0 to speak with an agent.
    </Say>
  </Gather>
</Response>
```

**Performance**:
- **Concurrent Calls**: 500
- **Average Handle Time**: 3 minutes
- **Automation Rate**: 68%
- **Speech Recognition Accuracy**: 94%

---

## Technical Implementation

### Deployment Architecture

```yaml
Kubernetes Namespace: presentation-layer

Services:
  - web-portal-svc:
      replicas: 5-15 (HPA based on CPU/memory)
      resources:
        requests: { cpu: 200m, memory: 512Mi }
        limits: { cpu: 1000m, memory: 2Gi }
      
  - mobile-api-svc:
      replicas: 3-8
      resources:
        requests: { cpu: 100m, memory: 256Mi }
        limits: { cpu: 500m, memory: 1Gi }
      
  - provider-portal-svc:
      replicas: 3-10
      resources:
        requests: { cpu: 200m, memory: 512Mi }
        limits: { cpu: 800m, memory: 1.5Gi }
      
  - edi-gateway-svc:
      replicas: 2-5
      resources:
        requests: { cpu: 150m, memory: 384Mi }
        limits: { cpu: 600m, memory: 1Gi }
      
  - fax-ocr-svc:
      replicas: 2-4
      resources:
        requests: { cpu: 500m, memory: 1Gi }
        limits: { cpu: 2000m, memory: 4Gi }
      
  - voice-ivr-svc:
      replicas: 2-3
      resources:
        requests: { cpu: 100m, memory: 256Mi }
        limits: { cpu: 400m, memory: 512Mi }

Ingress:
  Controller: nginx-ingress
  TLS: Let's Encrypt (cert-manager)
  Hostnames:
    - portal.pahealthcare.com
    - api.pahealthcare.com
    - provider.pahealthcare.com
```

### Load Balancing

**Azure Application Gateway (Layer 7)**:
- Path-based routing
- SSL termination
- Web Application Firewall (WAF)
- Cookie-based session affinity (if needed)

**Traffic Distribution**:
```
Web Portal:     60% of traffic (30,000 requests/day)
Mobile API:     25% of traffic (12,500 requests/day)
Provider Portal: 10% of traffic (5,000 requests/day)
EDI Gateway:     3% of traffic (1,500 requests/day)
Fax OCR:        1.5% of traffic (750 requests/day)
Voice IVR:      0.5% of traffic (250 calls/day)
```

---

## API Specifications

### Common API Patterns

**Authentication**:
```http
# All requests require JWT
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...

# JWT Payload
{
  "sub": "user-uuid-123",
  "role": "provider",
  "npi": "1234567890",
  "iat": 1717329000,
  "exp": 1717415400
}
```

**Rate Limiting**:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1717329060
```

**Error Responses**:
```json
{
  "error": {
    "code": "INVALID_MEMBER_ID",
    "message": "Member ID must be 10 digits starting with 'M-'",
    "details": {
      "field": "member_id",
      "value": "123456"
    }
  }
}
```

---

## Data Flow

### PA Submission Flow

```
1. User initiates PA request
   ↓
2. Frontend validates form
   ↓
3. POST /api/v1/pa/submit
   ↓
4. API Gateway (Auth + Rate Limit)
   ↓
5. Create case in PostgreSQL
   ↓
6. Upload documents to Azure Blob
   ↓
7. Publish event to Kafka (pa.case.created)
   ↓
8. Return case_id to user
   ↓
9. WebSocket notification ("PA submitted successfully")
```

### Real-Time Status Updates

```javascript
// WebSocket connection
const socket = io('wss://api.pahealthcare.com');

socket.on('connect', () => {
  socket.emit('subscribe', { case_id: 'PA-2026-123456' });
});

socket.on('pa_status_update', (data) => {
  // { case_id, status, timestamp, agent }
  console.log('Status:', data.status);
});
```

---

## Security & Compliance

### Authentication & Authorization

**OAuth 2.0 + OpenID Connect**:
- Provider: Keycloak
- Flows: Authorization Code, Client Credentials
- Scopes: `pa:submit`, `pa:read`, `pa:cancel`

**Role-Based Access Control (RBAC)**:
```yaml
Roles:
  - member:
      permissions: [pa:submit, pa:read_own]
  - provider:
      permissions: [pa:submit, pa:read_own, pa:bulk_submit]
  - payer_admin:
      permissions: [pa:read_all, pa:approve, pa:deny]
  - reviewer:
      permissions: [pa:read_all, pa:review]
```

### Data Protection

**Encryption**:
- **In Transit**: TLS 1.3
- **At Rest**: AES-256 (Azure Storage Service Encryption)

**PII/PHI Handling**:
- All requests logged with PHI redacted
- HIPAA compliance validation
- Data retention: 7 years (regulatory requirement)

### Security Headers

```http
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'
X-XSS-Protection: 1; mode=block
```

---

## Performance & Scaling

### Auto-Scaling Configuration

```yaml
HorizontalPodAutoscaler:
  web-portal-svc:
    minReplicas: 5
    maxReplicas: 15
    metrics:
      - type: Resource
        resource:
          name: cpu
          target: 70%
      - type: Resource
        resource:
          name: memory
          target: 80%
  
  mobile-api-svc:
    minReplicas: 3
    maxReplicas: 8
    metrics:
      - type: Pods
        pods:
          metric: http_requests_per_second
          target: 500
```

### Performance Metrics

| Service | P50 Latency | P95 Latency | P99 Latency | Throughput |
|---------|-------------|-------------|-------------|------------|
| Web Portal | 120ms | 450ms | 1.2s | 500 req/s |
| Mobile API | 45ms | 120ms | 350ms | 200 req/s |
| Provider Portal | 200ms | 600ms | 1.5s | 100 req/s |
| EDI Gateway | 250ms | 500ms | 800ms | 50 tx/s |
| Fax OCR | 18s | 32s | 45s | 5 fax/min |
| Voice IVR | 800ms | 1.5s | 3s | 10 calls/min |

---

## Monitoring & Operations

### Observability Stack

**Metrics**: Prometheus + Grafana
```yaml
Dashboards:
  - Presentation Layer Overview
    * Request rate per service
    * Error rate (4xx, 5xx)
    * Latency percentiles (P50, P95, P99)
    * Pod CPU/memory usage
  
  - User Journey Analytics
    * PA submission funnel
    * Form abandonment rate
    * Time to submit
    * Document upload success rate
```

**Logging**: Azure Log Analytics
```json
// Structured log format
{
  "timestamp": "2026-06-02T10:30:15.234Z",
  "service": "web-portal-svc",
  "level": "INFO",
  "message": "PA submitted successfully",
  "context": {
    "case_id": "PA-2026-123456",
    "user_id": "user-uuid-123",
    "duration_ms": 452
  }
}
```

**Tracing**: Jaeger (OpenTelemetry)
- Trace every PA submission end-to-end
- Distributed trace ID propagation
- Service dependency map

### Alerting

```yaml
Alerts:
  - name: HighErrorRate
    condition: error_rate > 5% for 5 minutes
    severity: critical
    action: PagerDuty
  
  - name: SlowResponseTime
    condition: p95_latency > 2s for 10 minutes
    severity: warning
    action: Slack
  
  - name: PodCrashLoop
    condition: pod_restarts > 5 in 10 minutes
    severity: critical
    action: PagerDuty
```

---

## Summary

The **Presentation Layer** handles **50,000 PA requests per day** across **6 different channels**, providing a seamless multi-channel experience for members, providers, and payers. It combines modern web technologies (React, Angular) with enterprise integrations (EDI, Fax, IVR) to serve as the critical entry point for the PA platform.

**Key Metrics**:
- **6 services** deployed on AKS
- **99.95% uptime** SLA
- **Sub-second response times** for web/mobile
- **98.5% OCR accuracy** for fax intake
- **94% speech recognition accuracy** for IVR
- **HIPAA compliant** with end-to-end encryption

# TapPay Integration Guide - Complete Reference

> **Last Updated**: 2025-11-29  
> **TapPay API Version**: V1.4 (2025/02)  
> **Status**: Production-ready  
> **Maintained By**: Duotopia Development Team

---

## Table of Contents

### Part I: Payment Integration
1. [Payment Setup & Configuration](#1-payment-setup--configuration)
2. [Staging Environment Testing](#2-staging-environment-testing)
3. [Payment Testing Guide](#3-payment-testing-guide)
4. [Subscription & Cancellation Policies](#4-subscription--cancellation-policies)

### Part II: E-Invoice Integration
5. [E-Invoice System Overview](#5-e-invoice-system-overview)
6. [API Integration Specification](#6-api-integration-specification)
7. [Database Design for E-Invoice](#7-database-design-for-e-invoice)
8. [Testing & Validation](#8-testing--validation)

### Part III: Production Operations
9. [Security Configuration](#9-security-configuration)
10. [Production Checklist](#10-production-checklist)
11. [Monitoring & Alerts](#11-monitoring--alerts)

---

# Part I: Payment Integration

## 1. Payment Setup & Configuration

### Environment Configuration

**Staging Environment** (Real card testing):
- Frontend: `VITE_TAPPAY_PRODUCTION_*` + `VITE_TAPPAY_SERVER_TYPE=production`
- Backend: `TAPPAY_ENV=production` + all production credentials

**Production Environment** (Real transactions):
- Frontend: `VITE_TAPPAY_PRODUCTION_*` + `VITE_TAPPAY_SERVER_TYPE=production`
- Backend: `TAPPAY_ENV=production` + all production credentials

**Local Development** (Sandbox testing):
- Frontend: `VITE_TAPPAY_SANDBOX_*` + `VITE_TAPPAY_SERVER_TYPE=sandbox`
- Backend: `TAPPAY_ENV=sandbox` + all sandbox credentials

### Required Credentials

```yaml
# GitHub Secrets (Backend)
TAPPAY_SANDBOX_APP_ID
TAPPAY_SANDBOX_APP_KEY
TAPPAY_SANDBOX_PARTNER_KEY
TAPPAY_SANDBOX_MERCHANT_ID

TAPPAY_PRODUCTION_APP_ID
TAPPAY_PRODUCTION_APP_KEY
TAPPAY_PRODUCTION_PARTNER_KEY
TAPPAY_PRODUCTION_MERCHANT_ID

# Build Arguments (Frontend)
VITE_TAPPAY_PRODUCTION_APP_ID
VITE_TAPPAY_PRODUCTION_APP_KEY
VITE_TAPPAY_SERVER_TYPE=production
```

---

## 2. Staging Environment Testing

### Test Environment URLs
- **Staging Frontend**: https://duotopia-staging-frontend-b2ovkkgl6a-de.a.run.app
- **Staging Backend**: https://duotopia-staging-backend-b2ovkkgl6a-de.a.run.app
- **TapPay Environment**: Sandbox (沙盒測試環境)
- **TapPay Merchant ID**: `***REDACTED***` (stored in environment variables)

### TapPay Portal Access
- **Portal URL**: https://portal.tappaysdk.com/
- **Environment**: Switch to "Sandbox" (右上角下拉選單)

---

## 3. Payment Testing Guide

### Step-by-Step Testing Flow

#### Step 1: User Registration & Login
1. Navigate to staging environment
2. Register new teacher account or use test account
3. Verify email and login

#### Step 2: Subscription Selection
**Test Plans**:
- 📅 **Monthly**: NT$ 399/month
- 📅 **Quarterly**: NT$ 1,097/quarter (20% off)
- 📅 **Yearly**: NT$ 3,588/year (25% off)

#### Step 3: Payment Information

**TapPay Test Cards** (Sandbox Environment):

| Purpose | Card Number | Expiry | CVV | Expected Result |
|---------|-------------|--------|-----|----------------|
| Successful Payment | `4242 4242 4242 4242` | 12/25 | 123 | ✅ Success |
| Insufficient Funds | `4000 0000 0000 0002` | 12/25 | 123 | ❌ Declined |
| Expired Card | `4000 0000 0000 0069` | 12/25 | 123 | ❌ Expired |
| Invalid CVV | `4000 0000 0000 0127` | 12/25 | 123 | ❌ CVV Error |

**Cardholder Name**: Test User (任意名稱)

#### Step 4: Confirm Payment
1. Click "Confirm Payment"
2. Wait for processing screen
3. Verify success message
4. Check subscription status updated

#### Step 5: TapPay Portal Verification
1. Login to TapPay Portal
2. Switch to Sandbox environment
3. Navigate to "Transaction Management" → "Transaction Records"
4. Verify transaction details:
   - Transaction time matches
   - Merchant ID: `***REDACTED***` (from environment variables)
   - Amount is correct
   - Status: Success
   - Card last 4 digits: 4242

### Test Cases Checklist

- [ ] **Successful Payment**
  - Use `4242 4242 4242 4242`
  - Frontend shows subscription success
  - TapPay portal has transaction record
  - Subscription status updated immediately

- [ ] **Subscription Status Update**
  - Payment triggers status change
  - Expiry date calculated correctly
  - Feature permissions enabled

- [ ] **TapPay Portal Reconciliation**
  - Transaction amount correct
  - Merchant ID correct
  - Order number traceable

- [ ] **Payment Failure Handling**
  - Use `4000 0000 0000 0002` for insufficient funds
  - Error message displayed
  - Subscription status unchanged

- [ ] **Multiple Renewals**
  - Test consecutive subscriptions
  - Verify expiry date accumulation

### Troubleshooting

**Q: Payment succeeded but subscription not updated?**
1. Refresh page
2. Check TapPay portal for transaction success
3. Contact dev team with error logs

**Q: TapPay portal shows no transaction?**
1. Confirm using Sandbox environment (not Production)
2. Check correct TapPay account login
3. Verify time range includes test time

---

## 4. Subscription & Cancellation Policies

### Current Implementation Status
- ✅ **Payment**: Fully implemented
- ⚠️ **Cancellation**: Policy decision required
- ⚠️ **Refunds**: Not yet implemented

### Cancellation Policy Options

#### Option A: Immediate Cancellation + Prorated Refund
**How it works**: User loses service immediately, refund based on remaining days

**Pros**: Fair to users, lower barrier to cancel  
**Cons**: Complex refund calculation, high customer service cost

**Example**: Spotify

#### Option B: End-of-Period Cancellation (Most Common) ⭐ **RECOMMENDED**
**How it works**:
- User cancels, service continues until current period ends
- No refund (user already paid, can use until end)
- Auto-renewal disabled

**Pros**:
- ✅ Good user experience
- ✅ No refund processing needed
- ✅ Simple implementation
- ✅ Industry standard

**Cons**: None

**Example**: Netflix, GitHub, Notion, Slack

**Frontend Display**:
```
您的訂閱將在 2025/12/31 到期後停止續訂。
在此之前,您仍可繼續使用所有功能。
```

#### Option C: Hybrid Model (7-day Grace Period) 🌟 **BEST FOR TAIWAN**
**How it works**:
- **Within 7 days**: Full refund + immediate service termination
- **After 7 days**: No refund + service until period end

**Pros**:
- ✅ Complies with Taiwan Consumer Protection Law (7-day cooling-off period)
- ✅ Reduces purchase risk
- ✅ Builds brand trust
- ✅ Reduces refund disputes

**Cons**: Medium implementation complexity

**Example**: Apple App Store, Google Play

### Taiwan Consumer Protection Law
**7-Day Cooling-Off Period**:
- Required for online purchases
- **Exception**: Digital content if already used may not apply
- **Recommendation**: Still provide 7-day refund to build trust

### Cancellation Decision Matrix

| Item | A: Immediate | B: End-of-Period | C: Hybrid (7-day) |
|------|-------------|-----------------|-------------------|
| User Experience | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Technical Complexity | 🔴 High | 🟢 Low | 🟡 Medium |
| Customer Service Cost | 🔴 High | 🟢 Low | 🟡 Medium |
| Brand Image | 🟡 Fair | 🟡 Fair | 🟢 Excellent |
| Industry Standard | ❌ Rare | ✅ Common | ✅ Common |

### Implementation Requirements (if Option C chosen)

**Database Fields**:
```python
cancel_at_period_end: bool  # End-of-period cancel flag
cancelled_at: datetime      # Cancellation timestamp
refund_eligible_until: datetime  # Refund deadline (purchase_date + 7 days)
```

**API Endpoints**:
```
POST /api/subscription/cancel  # Cancel subscription
POST /api/subscription/refund  # Request refund (within 7 days)
GET  /api/subscription/cancellation-policy  # Query policy
```

**Development Estimate**: 3 days total
- Database: 0.5 day
- Backend API: 1 day
- Frontend UI: 1 day
- Testing: 0.5 day

---

# Part II: E-Invoice Integration

## 5. E-Invoice System Overview

### System Architecture
```
Duotopia Platform
    ↓ (Payment Success)
TapPay Payment API
    ↓ (Auto-trigger)
TapPay E-Invoice API
    ↓ (Auto-process)
Cloud Mobile E-Invoice Center
    ↓ (Auto-send)
User Email
```

### Key Concepts
- **TapPay**: Payment processing, invoice API, invoice data storage
- **Cloud Mobile**: Upload to tax authority, email delivery
- **Duotopia**: Call TapPay invoice API, store `rec_invoice_id` and `invoice_number`

### TapPay Official Clarifications

#### Q1: Sandbox Test Invoice Numbers
**Question**: Does Sandbox already have test invoice numbers configured?

**TapPay Answer**:
> Test invoice numbers are pre-configured. No need to add them yourself. If running low, notify us to add more.

**Conclusion**: ✅ Can test directly in Sandbox, no setup needed

#### Q2: Notify Testing
**Question**: How to test Notify functionality in Sandbox?

**TapPay Answer**:
> Only abnormal situations trigger Notify. No test mechanism available currently.

**Conclusion**: ⚠️ Cannot proactively test Notify, only wait for actual errors

**Recommendation**:
- Implement robust error handling in Notify webhook
- Use ngrok or similar for local webhook testing
- Monitor Notify events in production via logging

#### Q3: Payment and Invoice Timing
**Question**: Issue invoice immediately after payment? Or wait for settlement?

**TapPay Answer**:
> Generally issue invoice upon payment completion. For refunds:
> - **Same Period**: Can void and reissue
> **Cross-Period**: Issue allowance

**Conclusion**: ✅ Payment Success → Issue Invoice Immediately

#### Q4: Recurring Subscription Invoicing
**Question**: Will TapPay handle recurring subscription invoicing automatically?

**TapPay Answer**:
> You must trigger via API, as recurring payments are also triggered by your API.

**Conclusion**: ✅ We need to implement scheduled billing

**Implementation**:
- Use Google Cloud Scheduler for monthly billing
- Call TapPay "Pay by Token" API
- Auto-issue invoice on successful charge
- Update subscription expiry date

---

## 6. API Integration Specification

### 6.1 Issue Invoice

**Timing**: Immediately after payment success

**Endpoint**: `POST /tpc/einvoice/issue`

**Request**:
```python
{
    "partner_key": PARTNER_KEY,
    "rec_trade_id": "xxx",  # From payment response
    
    # Buyer Information
    "buyer_email": "user@example.com",  # Required
    "buyer_tax_id": "",  # Required for B2B
    "buyer_name": "",    # Required for B2B
    
    # Carrier Information (B2C)
    "carrier_type": "",  # e.g., "3J0002" for mobile barcode
    "carrier_id": "",
    
    # Amount Information
    "sales_amount": 376,   # Excluding tax
    "tax_amount": 19,      # Tax (5%)
    "total_amount": 395,   # Total
    
    # Invoice Items
    "items": [{
        "item_name": "Duotopia Subscription",
        "item_count": 1,
        "item_price": 395,
        "item_tax_type": "TAXED"
    }],
    
    # Auto-send email
    "issue_notify_email": "AUTO"
}
```

**Response (Success)**:
```json
{
    "status": 0,
    "rec_invoice_id": "xxx",  # IMPORTANT: Store this
    "invoice_number": "AB12345678",
    "invoice_date": "2025-11-29"
}
```

### 6.2 Void Invoice (Same Period Only)

**Endpoint**: `POST /tpc/einvoice/void`

**Request**:
```python
{
    "partner_key": PARTNER_KEY,
    "rec_invoice_id": "xxx",
    "void_reason": "Order cancelled"
}
```

### 6.3 Issue Allowance (Cross-Period Refunds)

**Endpoint**: `POST /tpc/einvoice/allowance`

**Request**:
```python
{
    "partner_key": PARTNER_KEY,
    "rec_invoice_id": "xxx",
    
    # Allowance amount
    "allowance_sales_amount": 376,
    "allowance_tax_amount": 19,
    "allowance_total_amount": 395,
    
    # Reason
    "allowance_reason": "Partial refund",
    
    # Items
    "items": [{
        "item_name": "Subscription partial refund",
        "item_count": 1,
        "item_price": 395,
        "item_tax_type": "TAXED"
    }]
}
```

### 6.4 Query Invoice

**Endpoint**: `POST /tpc/einvoice/query`

**Request**:
```python
{
    "partner_key": PARTNER_KEY,
    "rec_invoice_id": "xxx"
}
```

---

## 7. Database Design for E-Invoice

### Main Table Extension

**Extend `teacher_subscription_transactions`**:
```sql
ALTER TABLE teacher_subscription_transactions ADD COLUMN (
    -- Invoice Core Information
    rec_invoice_id VARCHAR(30),        -- TapPay invoice ID (for void/query)
    invoice_number VARCHAR(10),         -- Invoice number (display to user)
    invoice_status VARCHAR(20) DEFAULT 'PENDING',
    invoice_issued_at TIMESTAMP,        -- For same-period vs cross-period logic
    
    -- Buyer Information
    buyer_tax_id VARCHAR(8),           -- Tax ID (B2B)
    buyer_name VARCHAR(100),           -- Buyer name (B2B)
    buyer_email VARCHAR(255) NOT NULL, -- Invoice email (required)
    
    -- Carrier Information (B2C)
    carrier_type VARCHAR(10),
    carrier_id VARCHAR(64),
    
    -- Full invoice response (backup/debug)
    invoice_response JSONB
);
```

### Invoice Status History Table

**Purpose**: Track invoice state changes for audit and Notify events

```sql
CREATE TABLE invoice_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL REFERENCES teacher_subscription_transactions(id) ON DELETE CASCADE,
    
    -- Status Change
    from_status VARCHAR(20),
    to_status VARCHAR(20) NOT NULL,
    
    -- Change Reason
    action_type VARCHAR(20) NOT NULL,  -- ISSUE/VOID/ALLOWANCE/REISSUE/NOTIFY
    reason TEXT,
    
    -- Notify Related
    is_notify BOOLEAN DEFAULT FALSE,
    notify_error_code VARCHAR(20),
    notify_error_msg TEXT,
    
    -- Full Data
    request_payload JSONB,
    response_payload JSONB,
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_transaction_id (transaction_id),
    INDEX idx_created_at (created_at DESC)
);
```

### Invoice Status Flow
```
PENDING (待開立)
  ↓
ISSUED (已開立) ← Invoice issued successfully
  ↓
├─ VOIDED (已作廢) ← Same-period void
├─ ALLOWANCED (已折讓) ← Cross-period refund
├─ REISSUED (已註銷重開) ← Correct information
└─ ERROR (異常) ← Notify error
```

---

## 8. Testing & Validation

### Sandbox Environment
- **Base URL**: `https://sandbox.tappaysdk.com`
- ✅ Test invoice numbers pre-configured
- ✅ Can test issue/void/allowance
- ⚠️ Cannot proactively test Notify

### Production Environment
- **Base URL**: `https://prod.tappaysdk.com`
- Requires production `partner_key`
- Requires Cloud Mobile configuration

### Testing Checklist

**Development Phase**:
- [ ] Implement Issue Invoice API
- [ ] Implement Void Invoice API
- [ ] Implement Allowance API
- [ ] Implement Query Invoice API
- [ ] Implement Notify Webhook
- [ ] Database migration complete
- [ ] Unit test coverage > 80%

**Testing Phase**:
- [ ] Sandbox complete test (issue/void/allowance/query)
- [ ] Test same-period refund (void and reissue)
- [ ] Test cross-period refund (allowance)
- [ ] Test recurring billing schedule
- [ ] Stress test (100 invoices)

**Production Phase**:
- [ ] Production Partner Key obtained
- [ ] Environment variables configured
- [ ] Notify URL configured
- [ ] BigQuery logging enabled
- [ ] Slack alerts configured
- [ ] Monitoring dashboard created

**Compliance Phase**:
- [ ] Taiwan E-Invoice regulations checked
- [ ] Tax ID validation logic
- [ ] Privacy protection measures
- [ ] Data retention policy (7+ years)

---

# Part III: Production Operations

## 9. Security Configuration

### Frontend Environment Variables (Build-time)
```yaml
# ⚠️ Must use PRODUCTION prefix
VITE_TAPPAY_PRODUCTION_APP_ID=xxx
VITE_TAPPAY_PRODUCTION_APP_KEY=xxx
VITE_TAPPAY_SERVER_TYPE=production

# ❌ WRONG: Will cause appKey = undefined
# VITE_TAPPAY_APP_ID=xxx
```

### Backend Environment Variables (Runtime)
```yaml
# Environment selector
TAPPAY_ENV=production  # or sandbox

# Dual environment credentials
TAPPAY_SANDBOX_APP_ID=xxx
TAPPAY_SANDBOX_APP_KEY=xxx
TAPPAY_SANDBOX_PARTNER_KEY=xxx
TAPPAY_SANDBOX_MERCHANT_ID=xxx

TAPPAY_PRODUCTION_APP_ID=xxx
TAPPAY_PRODUCTION_APP_KEY=xxx
TAPPAY_PRODUCTION_PARTNER_KEY=xxx
TAPPAY_PRODUCTION_MERCHANT_ID=xxx
```

---

## 10. Production Checklist

### Pre-Launch
- [ ] Production credentials verified
- [ ] TapPay Portal account configured
- [ ] Cloud Mobile account set up
- [ ] Invoice number allocation confirmed
- [ ] Notify webhook URL configured and tested

### Launch Day
- [ ] Monitor first real transaction
- [ ] Verify invoice issued correctly
- [ ] Check Cloud Mobile upload status
- [ ] Confirm email delivery
- [ ] Verify TapPay Portal reconciliation

### Post-Launch
- [ ] Daily transaction reconciliation
- [ ] Weekly invoice status check
- [ ] Monthly compliance review
- [ ] Quarterly security audit

---

## 11. Monitoring & Alerts

### Key Metrics to Monitor
1. **Payment Success Rate**: Target > 95%
2. **Invoice Issuance Rate**: Should be 100% of successful payments
3. **Notify Error Rate**: Should be < 1%
4. **Refund Processing Time**: Target < 24 hours
5. **Invoice Email Delivery**: Target > 99%

### Alert Configuration
- **Critical**: Payment failure rate > 5%
- **Critical**: Invoice issuance failure
- **Warning**: Slow query detection (invoice API > 2s)
- **Warning**: Notify error received
- **Info**: Daily reconciliation summary

### Logging Strategy
```python
# Log all invoice operations
logger.info(f"Invoice issued: {rec_invoice_id} for transaction {transaction_id}")
logger.warning(f"Slow invoice API: {duration}ms")
logger.error(f"Invoice issuance failed: {error}")

# Log Notify events
logger.error(f"TapPay Notify Error: {rec_invoice_id} - {error_msg}")

# Log to BigQuery for analytics
await log_to_bigquery({
    "event_type": "invoice_issued",
    "rec_invoice_id": rec_invoice_id,
    "amount": amount,
    "duration_ms": duration
})
```

---

## Reference Resources

### Official Documentation
- **TapPay E-Invoice API**: `docs/payment/電子發票Open_API規格_商戶_V1.4.pdf`
- **TapPay Portal Manual**: `docs/payment/TapPay後台 - E-invoice系統操作.pdf`
- **Taiwan E-Invoice Platform**: https://www.einvoice.nat.gov.tw/
- **Cloud Mobile**: https://www.cloud-mobile.com.tw/

### Internal Documentation
- **CI/CD Configuration**: [CICD.md](../../CICD.md)
- **Testing Guide**: [TESTING_GUIDE.md](../TESTING_GUIDE.md)

---

## Document Maintenance

**Document Version**: v2.0 (Merged from PAYMENT_TESTING_GUIDE.md + TAPPAY_EINVOICE_INTEGRATION.md)  
**Created Date**: 2024-10-21  
**Last Updated**: 2025-11-29  
**Maintained By**: Duotopia Development Team

This document will be updated as TapPay API evolves. Check version number regularly.

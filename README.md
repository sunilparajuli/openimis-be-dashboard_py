# openIMIS Backend Dashboard Reference Module

## Overview
This repository contains the backend implementation of the **openIMIS Dashboard reference module**.  
It provides **GraphQL queries and analytics resolvers** for visualizing healthcare claims data across multiple domains, including geospatial distribution, epidemiology, customer journey, operational performance, social protection, and financial indicators.  

The module is designed to support decision-making through **real-time dashboards** and **analytics aggregations**.

## Code Climate (develop branch)
TBD: Add Code Climate badge or status once integrated (e.g., maintainability, test coverage).

---

## GraphQL Types

### Geospatial Analytics
- **RegionSummaryType** – Region name, claim count, and total claimed amount.  
- **ProviderNetworkDetailType** – Facility and geographic hierarchy details.  
- **GeospatialAnalyticsGQLType** – Combines regional claim summaries and provider network distribution.

### Epidemiological Analytics
- **IcdSummaryType** – ICD disease name, claim count, and total cost.  
- **DiseaseTrendPointType** – Monthly disease claim trend.  
- **EpidemiologicalAnalyticsGQLType** – Summaries of top diseases by volume, cost, and trends.

### Customer Journey Analytics
- **ClaimLifecycleFunnelType** – Claim progression by stage (entered, checked, processed, paid).  
- **RejectionReasonSummaryType** – Top rejection reasons.  
- **ClaimPaymentTimeType** – Payment time distribution.  
- **CustomerJourneyAnalyticsGQLType** – Funnel analytics, rejection data, pending feedback, payment times.

### Operational Analytics
- **ClaimTurnaroundType** – Average processing time per facility.  
- **AdjusterPerformanceType** – Performance of claim adjusters.  
- **HealthFacilityQualityType** – Quality indicators for health facilities.  
- **OperationalAnalyticsGQLType** – Aggregated operational metrics.

### Social Protection Analytics
- **ProductClaimSummaryType** – Claim totals by insurance product.  
- **SubProductClaimSummaryType** – Claim totals by sub-product.  
- **ProductInsureeCountType** – Insuree coverage per product.  
- **SocialProtectionAnalyticsGQLType** – Coverage and protection indicators.

### General Analytics
- **TopClaimType** – Claim ID, code, amount, facility.  
- **HealthFacilityClaimSummaryType** – Facility-level financial totals.  
- **AnalyticsGQLType** – Top claims, high-value claims, and facility totals.

### Dashboard
- **DashboardGQLType** – A consolidated view with:  
  - Claim processing status  
  - Service types (inpatient, outpatient, emergency, referral)  
  - Facility levels (primary, secondary, tertiary, specialized)  
  - Financial metrics (claimed, approved, average, high-value claims)  
  - Quality indicators (feedback, reviews, attachments, pre-authorizations)  
  - Time-based metrics (monthly comparisons, processing efficiency rate)  

---

## GraphQL Queries

### `geospatialAnalytics`
- **Description**: Provides regional claim distribution and provider network mapping.  
- **Returns**: `GeospatialAnalyticsGQLType`.

### `epidemiologicalAnalytics`
- **Description**: Provides disease claim statistics and trends.  
- **Returns**: `EpidemiologicalAnalyticsGQLType`.

### `customerJourneyAnalytics`
- **Description**: Tracks claim lifecycle, rejections, and beneficiary experience.  
- **Returns**: `CustomerJourneyAnalyticsGQLType`.

### `operationalAnalytics`
- **Description**: Summarizes claim turnaround times, adjuster performance, and facility quality.  
- **Returns**: `OperationalAnalyticsGQLType`.

### `socialProtectionAnalytics`
- **Description**: Evaluates financial protection, vulnerable population coverage, and access equity.  
- **Returns**: `SocialProtectionAnalyticsGQLType`.

### `analytics`
- **Description**: Provides top claims and facility-level financial totals.  
- **Returns**: `AnalyticsGQLType`.

### `dashboard`
- **Description**: Consolidated healthcare claims dashboard metrics.  
- **Returns**: `DashboardGQLType`.

---

## Services / Resolvers

Resolvers in `schema/queries.py` implement optimized Django ORM queries with `annotate`, `aggregate`, and filtering on the `Claim` model to return structured analytics data.  
- Uses `TruncMonth` for trend analysis.  
- Aggregates claim data for performance, equity, and protection.  
- Includes demo data for some analytics where no direct computation is yet implemented.  

---

## Configuration Options

Configurable via `core.ModuleConfiguration`:  
- `dashboard.default_time_range`: Default time period for analytics queries (e.g., last 12 months).  
- `dashboard.top_claims_limit`: Maximum number of claims returned in `analytics` queries (Default: `10`).  
- `dashboard.financial_thresholds`: Thresholds for high-value or catastrophic claims. 
- `dashboard_per_hf`: filters dashboard elements by the Health Facility linked to the logged-in user (Default: `False`).

---

## openIMIS Module Dependencies
- `openimis-be-core_py`: Provides base models, utilities, and GraphQL integration.  
- `openimis-be-claim_py`: Required for claim models and processing logic.  
- `openimis-be-location_py`: Provides health facility and location hierarchy integration.  
